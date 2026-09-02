from __future__ import annotations

from types import SimpleNamespace

from ariadne.config import AppConfig, MongoConfig
from ariadne.mongo_store import RawDataStore
from ariadne.orchestrator import Orchestrator
from ariadne.models import Device

_TEST_DB = "ariadne_raw_test"
_TEST_COL = "bom_files_test"


def _store(enabled: bool = True) -> RawDataStore:
    if enabled:
        return RawDataStore(
            MongoConfig(uri="mongodb://localhost:27017", database=_TEST_DB, collection=_TEST_COL)
        )
    return RawDataStore(
        MongoConfig(uri="mongodb://invalid-host:27017", database=_TEST_DB, collection=_TEST_COL)
    )


class FakeCollection:
    def __init__(self):
        self.docs = []
        self.fail_insert = False

    def insert_one(self, doc):
        if self.fail_insert:
            raise Exception("insert failed")
        self.docs.append(doc)
        return SimpleNamespace(inserted_id=len(self.docs))

    def count_documents(self, filter=None):
        return len(self.docs)


class FakeAdmin:
    def command(self, cmd):
        return {"ok": 1}


class _FailingAdmin:
    def command(self, cmd):
        raise Exception("ping failed")


class FakeDB:
    def __init__(self, collection):
        self._collection = collection

    def __getitem__(self, name):
        return self._collection


class FakeClient:
    def __init__(self, collection, fail_ping=False):
        self._collection = collection
        self.closed = False
        self.admin = FakeAdmin() if not fail_ping else _FailingAdmin()

    def __getitem__(self, name):
        return FakeDB(self._collection)

    def __setitem__(self, name, value):
        pass

    def close(self):
        self.closed = True


def _monkeypatch_client(monkeypatch, client):
    monkeypatch.setattr("ariadne.mongo_store.MongoClient", lambda uri, **kw: client)


class TestRawDataStore:
    def test_offline_is_available_false(self):
        s = _store(enabled=False)
        try:
            assert s.available is False
        finally:
            s.close()

    def test_store_returns_none_when_offline(self):
        s = _store(enabled=False)
        try:
            doc_id = s.store("test.csv", "csv", "R1,10k,0603")
            assert doc_id is None
        finally:
            s.close()

    def test_count_zero_when_offline(self):
        s = _store(enabled=False)
        try:
            assert s.count() == 0
        finally:
            s.close()

    def test_hash_stable(self):
        assert RawDataStore._content_hash("abc") == RawDataStore._content_hash("abc")
        assert RawDataStore._content_hash("abc") != RawDataStore._content_hash("abd")

    def test_close_is_idempotent(self):
        s = _store(enabled=False)
        s.close()
        s.close()


class TestOrchestratorRawIntegration:
    def _orch(self, mongo_uri: str, tmp_db: str) -> Orchestrator:
        config = AppConfig.from_env()
        config.database.url = f"sqlite:///{tmp_db}"
        config.mongo = MongoConfig(uri=mongo_uri, database=_TEST_DB, collection=_TEST_COL)
        return Orchestrator(config)

    def test_offline_csv_import_still_works(self, tmp_path):
        csv = tmp_path / "bom.csv"
        csv.write_text("Ref,Qty,Value,Footprint\nR1,1,10k,0603\nC1,2,100nF,0402\n", encoding="utf-8")
        orch = self._orch("mongodb://invalid-host:27017", tmp_path / "a.db")
        try:
            result = orch.process_file(str(csv), Device(brand="T", model_name="M"))
            assert result.success
            assert result.imported_rows == 2
            assert orch._raw.available is False
            stats = orch.get_stats()
            assert stats["raw_documents"] == 0
            assert stats["raw_available"] is False
        finally:
            orch.close()

    def test_online_csv_import_stores_raw(self, tmp_path):
        csv = tmp_path / "bom.csv"
        csv.write_text("Ref,Qty,Value,Footprint\nR1,1,10k,0603\n", encoding="utf-8")
        orch = self._orch("mongodb://localhost:27017", tmp_path / "b.db")
        try:
            result = orch.process_file(str(csv), Device(brand="T", model_name="M"))
            assert result.success
            if not orch._raw.available:
                return
            try:
                stats = orch.get_stats()
                assert stats["raw_documents"] >= 1
                assert stats["raw_available"] is True
            finally:
                try:
                    from pymongo import MongoClient
                    mc = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=1000)
                    mc.drop_database(_TEST_DB)
                    mc.close()
                except Exception:
                    pass
        finally:
            orch.close()


class TestRawDataStoreOnline:
    def test_connect_success_sets_available(self, monkeypatch):
        coll = FakeCollection()
        _monkeypatch_client(monkeypatch, FakeClient(coll))
        s = _store(enabled=True)
        try:
            assert s.available is True
            assert s._collection is coll
        finally:
            s.close()

    def test_store_returns_object_id(self, monkeypatch):
        coll = FakeCollection()
        _monkeypatch_client(monkeypatch, FakeClient(coll))
        s = _store(enabled=True)
        try:
            doc_id = s.store("f.csv", "csv", "R1,10k", {"device": "X"})
            assert doc_id is not None
            assert len(coll.docs) == 1
            assert coll.docs[0]["filename"] == "f.csv"
            assert coll.docs[0]["file_format"] == "csv"
            assert coll.docs[0]["content_hash"] == RawDataStore._content_hash("R1,10k")
            assert coll.docs[0]["metadata"]["device"] == "X"
            assert "created_at" in coll.docs[0]
        finally:
            s.close()

    def test_count_after_store(self, monkeypatch):
        coll = FakeCollection()
        _monkeypatch_client(monkeypatch, FakeClient(coll))
        s = _store(enabled=True)
        try:
            assert s.count() == 0
            s.store("a.csv", "csv", "x")
            s.store("b.csv", "csv", "y")
            assert s.count() == 2
        finally:
            s.close()

    def test_store_insert_failure_returns_none(self, monkeypatch):
        coll = FakeCollection()
        coll.fail_insert = True
        _monkeypatch_client(monkeypatch, FakeClient(coll))
        s = _store(enabled=True)
        try:
            assert s.available is True
            assert s.store("f.csv", "csv", "x") is None
        finally:
            s.close()

    def test_close_closes_client(self, monkeypatch):
        coll = FakeCollection()
        client = FakeClient(coll)
        _monkeypatch_client(monkeypatch, client)
        s = _store(enabled=True)
        s.close()
        assert client.closed is True
        assert s.available is False

    def test_ping_failure_disables_store(self, monkeypatch):
        coll = FakeCollection()
        _monkeypatch_client(monkeypatch, FakeClient(coll, fail_ping=True))
        s = _store(enabled=True)
        try:
            assert s.available is False
            assert s._client is None
            assert s.store("f.csv", "csv", "x") is None
        finally:
            s.close()