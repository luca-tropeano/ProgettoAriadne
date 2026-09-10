from __future__ import annotations

from pathlib import Path

import pytest

from ariadne.config import AppConfig, DatabaseConfig
from ariadne.database import Database
from ariadne.mdf_auto import auto_source_mdf
from ariadne.models import BOMEntry, Device

TESTS_DIR = Path(__file__).resolve().parent
MDF_DIR = TESTS_DIR.parent / "test_data" / "mdf"


@pytest.fixture()
def db(tmp_path):
    cfg = AppConfig(database=DatabaseConfig(url=f"sqlite:///{tmp_path / 'auto.db'}"))
    database = Database(cfg.database)
    yield database
    database.close()


def _seed_device(db: Database):
    did = db.find_or_create_device(Device(brand="Test", model_name="AUTO-DEV", manufacturer="M"))
    db.insert_bom_entry(
        did,
        BOMEntry(item_number=1, quantity=2, reference_designator="C1,C5",
                 part_value="100nF", mounting_type="SMT",
                 manufacturer="KEMET", manufacturer_order_code="C0603C104K5RACTU",
                 package="0603"),
    )
    db.insert_bom_entry(
        did,
        BOMEntry(item_number=2, quantity=1, reference_designator="C2",
                 part_value="100nF", mounting_type="SMT",
                 manufacturer="MURATA", manufacturer_order_code="GCJ188R71H104KA12",
                 package="0603"),
    )
    db.insert_bom_entry(
        did,
        BOMEntry(item_number=3, quantity=1, reference_designator="R99",
                 part_value="DNF", mounting_type="SMT",
                 manufacturer="", manufacturer_order_code="DNF"),
    )
    return did


def test_auto_source_mdf_family_reference_nomdn(db):
    _seed_device(db)
    res = auto_source_mdf(db, "AUTO-DEV", mdf_dir=MDF_DIR)

    # KEMET MLCC → family MCD (6 sostanze dichiarate nel MCD-Ceramic.pdf)
    assert res.family_groups == 1
    assert res.files == ["MCD-Ceramic.pdf"]
    assert res.materials_created >= 6
    assert res.links_created == 6  # una BOMEntry (C1,C5) × 6 sostanze

    # MURATA → riferimento conformità annotato sulla BOMEntry, non linkato
    assert res.reference_components == 1
    murata = db.get_bom_entries(db.get_device("AUTO-DEV")["id"])[1]
    assert "MDF: https://www.murata.com/" in murata["notes"]

    # genereico DNF → no_mpn, nessun link
    assert res.no_mpn_components == 1
    assert "MDF:" not in (db.get_bom_entries(db.get_device("AUTO-DEV")["id"])[2]["notes"] or "")

    # i link sono nel DB: la BOMEntry (C1,C5) ha i 6 materiali di famiglia
    did = db.get_device("AUTO-DEV")["id"]
    assert len(db.get_component_material_links(did)) == 6


def test_auto_source_mdf_idempotent(db):
    _seed_device(db)
    first = auto_source_mdf(db, "AUTO-DEV", mdf_dir=MDF_DIR)
    second = auto_source_mdf(db, "AUTO-DEV", mdf_dir=MDF_DIR)

    assert first.links_created == 6
    assert second.links_created == 0
    assert second.materials_created == 0
    assert not second.warnings


def test_auto_source_mdf_missing_family_file_warns(db, tmp_path):
    _seed_device(db)
    empty = tmp_path / "empty_mdf"
    empty.mkdir()
    res = auto_source_mdf(db, "AUTO-DEV", mdf_dir=empty)
    assert res.family_groups == 1
    assert res.skipped_missing_mcd == 1
    assert any("MCD-Ceramic.pdf" in w for w in res.warnings)
    assert res.links_created == 0


def test_auto_source_mdf_unknown_device(db):
    res = auto_source_mdf(db, "NOT-EXISTS", mdf_dir=MDF_DIR)
    assert res.links_created == 0
    assert any("non trovato" in w for w in res.warnings)