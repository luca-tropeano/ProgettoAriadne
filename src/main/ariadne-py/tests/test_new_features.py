from __future__ import annotations

import os
import tempfile

import pytest

from ariadne.config import DatabaseConfig
from ariadne.database import Database, _resolve_db_path
from ariadne.eec import classify_all, classify_designator, eec_name
from ariadne.export import export_device_to_excel
from ariadne.models import BOMEntry, Device, Material


def _db():
    path = tempfile.mktemp(suffix=".db")
    db = Database(DatabaseConfig(url=f"sqlite:///{path}"))
    return db, path


def _device(db: Database, model: str = "TEST") -> int:
    return db.find_or_create_device(Device(model_name=model, brand="T"))


def _entry(**kw) -> BOMEntry:
    defaults = dict(item_number=1, quantity=1, reference_designator="R1")
    defaults.update(kw)
    return BOMEntry(**defaults)


class TestDBPathResolution:
    def test_absolute_path_kept(self, tmp_path):
        assert _resolve_db_path(f"sqlite:///{tmp_path / 'x.db'}") == str(tmp_path / "x.db")

    def test_memory_kept(self):
        assert _resolve_db_path("sqlite:///:memory:") == ":memory:"

    def test_relative_resolves_to_package_dir(self, tmp_path, monkeypatch):
        # lancia con CWD altrove: il path relativo NON deve dipendere dalla CWD
        monkeypatch.chdir(tmp_path)
        resolved = _resolve_db_path("sqlite:///rel_check.db")
        assert resolved == os.path.join(__import__("ariadne.database", fromlist=["PROJECT_ROOT"]).PROJECT_ROOT, "rel_check.db")

    def test_creates_missing_parent_dir(self, monkeypatch):
        import ariadne.database as dbmod
        monkeypatch.setattr(dbmod, "PROJECT_ROOT", tempfile.mkdtemp())
        resolved = dbmod._resolve_db_path("sqlite:///sub/dir_creato/test.db")
        assert os.path.isdir(os.path.dirname(resolved))
        assert resolved.endswith(os.path.join("sub", "dir_creato", "test.db"))


class TestDuplicateCheck:
    def test_insert_first_succeeds(self):
        db, path = _db()
        try:
            did = _device(db)
            entry_id = db.insert_bom_entry(did, _entry())
            assert entry_id is not None
        finally:
            db.close()
            os.unlink(path)

    def test_insert_duplicate_returns_none(self):
        db, path = _db()
        try:
            did = _device(db)
            db.insert_bom_entry(did, _entry())
            result = db.insert_bom_entry(did, _entry())
            assert result is None
        finally:
            db.close()
            os.unlink(path)

    def test_different_designators_both_insert(self):
        db, path = _db()
        try:
            did = _device(db)
            db.insert_bom_entry(did, _entry(reference_designator="R1"))
            result = db.insert_bom_entry(did, _entry(reference_designator="R2"))
            assert result is not None
        finally:
            db.close()
            os.unlink(path)

    def test_same_designator_different_device_both_insert(self):
        db, path = _db()
        try:
            did1 = _device(db, "DEV1")
            did2 = _device(db, "DEV2")
            db.insert_bom_entry(did1, _entry())
            result = db.insert_bom_entry(did2, _entry())
            assert result is not None
        finally:
            db.close()
            os.unlink(path)


class TestEECClassification:
    def test_resistor(self):
        assert classify_designator("R") == 1
        assert classify_designator("R1") == 1

    def test_capacitor(self):
        assert classify_designator("C") == 2
        assert classify_designator("C100") == 2

    def test_inductor(self):
        assert classify_designator("L") == 3

    def test_diode(self):
        assert classify_designator("D") == 4

    def test_transistor(self):
        assert classify_designator("Q") == 5

    def test_ic(self):
        assert classify_designator("U") == 6

    def test_connector(self):
        assert classify_designator("J") == 7
        assert classify_designator("CN") == 7

    def test_led(self):
        assert classify_designator("LED") == 12

    def test_unknown_is_other(self):
        assert classify_designator("ZZ") == 16

    def test_empty_is_none(self):
        assert classify_designator("") is None

    def test_classify_all_mixed(self):
        result = classify_all("R1,R2,C1,C2,C3,U1")
        assert result == 2

    def test_classify_all_single(self):
        assert classify_all("R1") == 1

    def test_eec_name(self):
        assert eec_name(1) == "Resistors"
        assert eec_name(99) == "Other"


class TestDeviceUpdate:
    def test_update_changes_fields(self):
        db, path = _db()
        try:
            did = _device(db, "ORIG")
            assert db.update_device(did, brand="B2", model_name="NUOVO",
                                    manufacturer="M2", year_of_production=2025,
                                    notes="n")
            dev = db.get_device_by_id(did)
            assert dev["model_name"] == "NUOVO"
            assert dev["brand"] == "B2"
            assert dev["year_of_production"] == 2025
            assert dev["notes"] == "n"
        finally:
            db.close()
            os.unlink(path)

    def test_update_missing_id_returns_false(self):
        db, path = _db()
        try:
            assert db.update_device(4242, model_name="X") is False
        finally:
            db.close()
            os.unlink(path)


class TestDeviceDelete:
    def test_delete_removes_device_entries_and_links(self):
        db, path = _db()
        try:
            did = _device(db)
            eid = db.insert_bom_entry(did, _entry(reference_designator="R1"))
            mid = db.insert_material(Material(material_name="lead", category="element"))
            db.link_material(eid, mid)
            assert db.delete_device(did) is True
            assert db.get_device_by_id(did) is None
            assert db.get_bom_entries(did) == []
        finally:
            db.close()
            os.unlink(path)

    def test_delete_missing_id_returns_false(self):
        db, path = _db()
        try:
            assert db.delete_device(4242) is False
        finally:
            db.close()
            os.unlink(path)


class TestExport:
    def test_export_creates_file(self):
        db, path = _db()
        try:
            did = _device(db)
            db.insert_bom_entry(did, _entry(item_number=1, reference_designator="R1", part_value="10k"))
            db.insert_bom_entry(did, _entry(item_number=2, reference_designator="C1", part_value="100nF"))
            out = tempfile.mktemp(suffix=".xlsx")
            export_device_to_excel(db, did, out)
            assert os.path.exists(out)
            assert os.path.getsize(out) > 0
            os.unlink(out)
        finally:
            db.close()
            os.unlink(path)

    def test_export_empty_device(self):
        db, path = _db()
        try:
            did = _device(db)
            out = tempfile.mktemp(suffix=".xlsx")
            export_device_to_excel(db, did, out)
            assert os.path.exists(out)
            os.unlink(out)
        finally:
            db.close()
            os.unlink(path)
