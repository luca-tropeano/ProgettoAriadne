from __future__ import annotations

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