from __future__ import annotations

import os
import tempfile

import pytest

from ariadne.config import DatabaseConfig
from ariadne.database import Database
from ariadne.eec import classify_all, classify_designator, eec_name
from ariadne.export import export_device_to_excel
from ariadne.models import BOMEntry, Device


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
