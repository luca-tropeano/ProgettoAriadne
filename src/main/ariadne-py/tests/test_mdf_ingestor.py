from __future__ import annotations

from pathlib import Path

import pytest

from ariadne.config import AppConfig, DatabaseConfig
from ariadne.database import Database
from ariadne.ipc1752 import DeclaredSubstance, parse_class_d_xml
from ariadne.mdf_ingestor import MDFIngestor, _substance_mass_mg
from ariadne.mdf_pdf_parser import PdfMdf
from ariadne.models import BOMEntry, Device, Material


def _sample_xml() -> Path:
    return Path(__file__).resolve().parent.parent / "test_data" / "mdf_class_d_sample.xml"


def _zvei_pdf() -> Path:
    return Path(__file__).resolve().parent.parent / "test_data" / "mdf_zvei_mlcc_example.pdf"


@pytest.fixture()
def db(tmp_path):
    cfg = AppConfig(database=DatabaseConfig(url=f"sqlite:///{tmp_path / 'mdf.db'}"))
    database = Database(cfg.database)
    yield database
    database.close()


def _seed_device(db):
    did = db.find_or_create_device(Device(brand="Test", model_name="MDF-DEV", manufacturer="M"))
    db.insert_bom_entry(
        did,
        BOMEntry(item_number=1, quantity=2, reference_designator="C1",
                 part_value="47nF", mounting_type="SMT"),
    )
    db.insert_bom_entry(
        did,
        BOMEntry(item_number=2, quantity=1, reference_designator="R1", mounting_type="THT"),
    )
    return did


def test_insert_material_dedupes(db):
    m1 = Material(material_name="Copper", casrn="7440-50-8", category="element")
    m2 = Material(material_name="Copper", casrn="7440-50-8", category="element")
    assert db.insert_material(m1) is not None
    assert db.insert_material(m2) is None
    assert db.get_material_id("Copper") is not None


def test_get_materials_counts_links(db):
    did = _seed_device(db)
    mid = db.insert_material(Material(material_name="Copper", category="element"))
    entry = db.find_bom_entry_by_ref(did, "R1")
    db.link_material(entry["id"], mid, mass_mg=1.5, source_mdf="MDF.pdf")
    rows = db.get_materials()
    assert len(rows) == 1
    assert rows[0]["material_name"] == "Copper"
    assert rows[0]["linked_entries"] == 1


def test_get_component_material_links(db):
    did = _seed_device(db)
    mid_copper = db.insert_material(Material(material_name="Copper", category="element"))
    mid_ceramic = db.insert_material(
        Material(material_name="Barium titanate", casrn="12047-27-7", category="ceramic")
    )
    c1 = db.find_bom_entry_by_ref(did, "C1")
    r1 = db.find_bom_entry_by_ref(did, "R1")
    db.link_material(c1["id"], mid_ceramic, mass_mg=5.2, note="IPC", source_mdf="class_d.xml")
    db.link_material(c1["id"], mid_copper, mass_mg=1.0, source_mdf="class_d.xml")
    db.link_material(r1["id"], mid_copper, mass_mg=0.5)

    rows = db.get_component_material_links()
    assert len(rows) == 3
    # filtro per device
    rows_dev = db.get_component_material_links(device_id=did)
    assert len(rows_dev) == 3
    # device inesistente
    assert db.get_component_material_links(device_id=99999) == []

    copper_rows = [r for r in rows if r["material_name"] == "Copper"]
    assert len(copper_rows) == 2
    ceramic = [r for r in rows if r["material_name"] == "Barium titanate"][0]
    assert ceramic["casrn"] == "12047-27-7"
    assert ceramic["mass_mg"] == 5.2
    assert ceramic["source_mdf"] == "class_d.xml"
    assert ceramic["note"] == "IPC"
    assert ceramic["model_name"] == "MDF-DEV"
    assert ceramic["reference_designator"] in ("C1", "R1")


def test_link_material_dedupes(db):
    did = _seed_device(db)
    mid = db.insert_material(Material(material_name="Copper", category="element"))
    entry = db.find_bom_entry_by_ref(did, "R1")
    assert db.link_material(entry["id"], mid) is not None
    assert db.link_material(entry["id"], mid) is None


def test_find_bom_entry_by_ref_group(db):
    did = _seed_device(db)
    db.insert_bom_entry(
        did,
        BOMEntry(item_number=3, quantity=3, reference_designator="C2,C3,C4", mounting_type="SMT"),
    )
    assert db.find_bom_entry_by_ref(did, "C3")["reference_designator"] == "C2,C3,C4"
    assert db.find_bom_entry_by_ref(did, "ZZ") is None
    assert db.find_bom_entry_by_ref(did, "  ") is None


def test_ingest_json_creates_and_links(db, tmp_path):
    _seed_device(db)
    payload = {
        "device_model": "MDF-DEV",
        "materials": [
            {"material_name": "Copper", "casrn": "7440-50-8", "category": "element"},
            {"material_name": "Tantalum", "casrn": "7440-25-7", "category": "element"},
        ],
        "links": [
            {"reference_designator": "C1", "material_name": "Copper",
             "mass_mg": 12.5, "note": "stub", "source_mdf": "MDF_KEMET_C0603.pdf"},
            {"reference_designator": "C1", "material_name": "Copper",
             "mass_mg": 9.0, "source_mdf": "MDF_2.pdf"},
        ],
    }
    p = tmp_path / "mdf.json"
    p.write_text(__import__("json").dumps(payload), encoding="utf-8")

    ing = MDFIngestor(db)
    res = ing.ingest_from_json(str(p))
    assert res.materials_created == 2
    assert res.materials_skipped == 0
    assert res.links_created == 1
    assert res.links_skipped == 1  # secondo link = duplicato
    assert db.get_materials()[0]["linked_entries"] == 1


def test_ingest_json_unknown_device_warns(db, tmp_path):
    payload = {
        "device_model": "NON-ESISTE",
        "materials": [{"material_name": "Copper", "category": "element"}],
        "links": [{"reference_designator": "R1", "material_name": "Copper"}],
    }
    p = tmp_path / "mdf.json"
    p.write_text(__import__("json").dumps(payload), encoding="utf-8")
    res = MDFIngestor(db).ingest_from_json(str(p))
    assert any("non trovato" in w for w in res.warnings)
    assert res.links_created == 0


def test_ingest_pdf_parses_real_fixture(db):
    """MDF PDF reale ZVEI: 4 sostanze dichiarabili, nessun part number → warning."""
    res = MDFIngestor(db).ingest_from_pdf(str(_zvei_pdf()))
    assert res.materials_created == 4
    assert res.links_created == 0
    assert any("Nessun part number" in w for w in res.warnings)
    names = {m["material_name"] for m in db.get_materials()}
    assert names == {"barium", "nickel", "copper", "tin"}


def test_ingest_pdf_links_by_part_number(db, monkeypatch):
    did = db.find_or_create_device(
        Device(brand="e-radionica", model_name="Inkplate 5", manufacturer="e-radionica")
    )
    db.insert_bom_entry(
        did,
        BOMEntry(item_number=1, quantity=2, reference_designator="C14,C15",
                 part_value="2u2-GRM188R61E225MA12D", package="0603C", mounting_type="SMT"),
    )
    fake = PdfMdf(
        component_name="CAP CER",
        total_mass_mg=6.3,
        substances=[
            DeclaredSubstance(name="Barium titanate", cas="12047-27-7", mass_mg=2.4,
                              concentration_pct=55.0),
            DeclaredSubstance(name="Nickel", cas="7440-02-0", mass_mg=3.449,
                              concentration_pct=100.0),
        ],
        part_numbers=["GRM188R61E225MA12D"],
    )
    monkeypatch.setattr("ariadne.mdf_ingestor.parse_pdf_mdf", lambda path: fake)
    res = MDFIngestor(db).ingest_from_pdf("mdf.pdf")
    assert res.materials_created == 2
    assert res.links_created == 2
    assert res.links_skipped == 0
    assert not res.warnings


def test_ingest_dispatches_by_extension(db, tmp_path):
    p = tmp_path / "mdf.json"
    p.write_text('{"materials": [{"material_name": "Cu", "category": "element"}]}', encoding="utf-8")
    res = MDFIngestor(db).ingest(str(p))
    assert res.materials_created == 1
    res_xml = MDFIngestor(db).ingest(str(_sample_xml()))
    assert res_xml.materials_created == 7
    res_pdf = MDFIngestor(db).ingest(str(_zvei_pdf()))
    assert res_pdf.materials_created == 4
    with pytest.raises(NotImplementedError):
        MDFIngestor(db).ingest("datasheet.xyz")


def test_parse_class_d_sample():
    products = parse_class_d_xml(_sample_xml().read_text(encoding="utf-8"))
    assert len(products) == 1
    product = products[0]
    assert product.product_name == "CAP CER 2.2UF 25V X5R 0603"
    assert "GRM188R61E225MA12D" in product.item_numbers
    assert len(product.homogeneous_materials) == 3

    all_subs = [s for hm in product.homogeneous_materials for s in hm.substances]
    assert len(all_subs) == 7
    lead = next(s for s in all_subs if s.name == "Lead")
    assert lead.cas == "7439-92-1"
    assert lead.mass_mg == pytest.approx(0.00234)
    assert lead.concentration_pct == pytest.approx(0.045)
    nickel_oxide = next(s for s in all_subs if s.name == "Nickel oxide")
    assert nickel_oxide.mass_mg is None
    assert nickel_oxide.concentration_pct == pytest.approx(3.5)


def test_parse_class_d_rejects_non_1752():
    with pytest.raises(ValueError):
        parse_class_d_xml("<foo><bar/></foo>")
    with pytest.raises(ValueError):
        parse_class_d_xml("<MainDeclaration><Product/></MainDeclaration>")


def test_substance_mass_mg_priority():
    assert _substance_mass_mg(
        DeclaredSubstance(name="X", mass_mg=0.00234, concentration_pct=0.045), 5.2
    ) == pytest.approx(0.00234)
    assert _substance_mass_mg(
        DeclaredSubstance(name="Y", mass_mg=None, concentration_pct=3.5), 5.2
    ) == pytest.approx(0.182)
    assert _substance_mass_mg(DeclaredSubstance(name="Z"), None) == 0.0


def test_ingest_xml_creates_and_links_by_part_number(db):
    did = db.find_or_create_device(
        Device(brand="e-radionica", model_name="Inkplate 5", manufacturer="e-radionica")
    )
    db.insert_bom_entry(
        did,
        BOMEntry(item_number=1, quantity=2, reference_designator="C14,C15",
                 part_value="2u2-GRM188R61E225MA12D", package="0603C", mounting_type="SMT"),
    )
    res = MDFIngestor(db).ingest_from_xml(str(_sample_xml()))
    assert res.materials_created == 7
    assert res.materials_skipped == 0
    assert res.links_created == 7
    assert res.links_skipped == 0
    assert not res.warnings
    lead = [m for m in db.get_materials() if m["material_name"] == "Lead"][0]
    assert lead["linked_entries"] == 1
    assert lead["casrn"] == "7439-92-1"


def test_ingest_xml_unknown_part_warns(db, tmp_path):
    xml_text = _sample_xml().read_text(encoding="utf-8").replace(
        "GRM188R61E225MA12D", "PART-NON-ESISTE"
    )
    p = tmp_path / "mdf_unknown.xml"
    p.write_text(xml_text, encoding="utf-8")
    res = MDFIngestor(db).ingest_from_xml(str(p))
    assert res.materials_created == 7
    assert res.links_created == 0
    assert any("non trovato" in w for w in res.warnings)


def test_ingest_xml_dedupes_on_second_run(db):
    did = db.find_or_create_device(
        Device(brand="e-radionica", model_name="Inkplate 5", manufacturer="e-radionica")
    )
    db.insert_bom_entry(
        did,
        BOMEntry(item_number=1, quantity=2, reference_designator="C14,C15",
                 part_value="2u2-GRM188R61E225MA12D", package="0603C", mounting_type="SMT"),
    )
    ing = MDFIngestor(db)
    first = ing.ingest_from_xml(str(_sample_xml()))
    second = ing.ingest_from_xml(str(_sample_xml()))
    assert first.links_created == 7
    assert second.materials_created == 0
    assert second.materials_skipped == 7
    assert second.links_created == 0
    assert second.links_skipped == 7