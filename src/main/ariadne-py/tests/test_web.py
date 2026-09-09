from __future__ import annotations

import io
from pathlib import Path

import pytest

from ariadne.config import AppConfig, DatabaseConfig, MongoConfig
from ariadne.database import Database
from ariadne.models import BOMEntry, Device
from ariadne.web import create_app

FIXTURES = Path(__file__).parent.parent / "test_data"


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'test_web.db'}"
    config = AppConfig(
        database=DatabaseConfig(url=db_url),
        mongo=MongoConfig(uri="mongodb://localhost:27017", database="ariadne_raw", collection="bom_files", from_env=True),
    )
    # seed un device
    db = Database(config.database)
    did = db.find_or_create_device(Device(brand="Test", model_name="WEB-DEV", manufacturer="TestMfg"))
    db.insert_bom_entry(
        did,
        BOMEntry(item_number=1, quantity=2, reference_designator="R1,R2", part_value="10k",
                 package="0603", manufacturer="M", mounting_type="SMT", eec_category_id=1),
    )
    db.close()
    return create_app(config)


@pytest.fixture()
def client(app):
    app.config["TESTING"] = True
    return app.test_client()


def test_index_lists_devices(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"WEB-DEV" in resp.data


def test_import_page_get(client):
    resp = client.get("/import")
    assert resp.status_code == 200
    assert b"Import BOM" in resp.data


def test_import_page_post_rejects_bad_ext(client):
    resp = client.post("/import", data={"bom_file": (io.BytesIO(b"x"), "foo.txt")},
                       content_type="multipart/form-data")
    # redirect alla stessa pagina con flash error
    assert resp.status_code == 302
    assert "/import" in resp.headers["Location"]


def test_import_page_post_with_csv(client, tmp_path):
    csv_path = Path(FIXTURES) / "inkplate5_bom.csv"
    with open(csv_path, "rb") as fh:
        data = {"brand": "Test", "model": "WEB-CSV", "manufacturer": "M", "bom_file": (fh, "inkplate5_bom.csv")}
        resp = client.post("/import", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302
    assert "/device/" in resp.headers["Location"]


def test_device_detail_shows_eec(client):
    # scalar device id 1 semina device "WEB-DEV"
    resp = client.get("/device/1")
    assert resp.status_code == 200
    assert b"WEB-DEV" in resp.data


def test_device_detail_missing_redirects(client):
    resp = client.get("/device/99999")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_export_excel(client, tmp_path):
    resp = client.get("/device/1/export")
    assert resp.status_code == 200
    assert resp.mimetype.startswith("application/vnd.openxmlformats")
    assert resp.data[:2] == b"PK"  # xlsx zip magic


def test_stats_json(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["devices"] >= 1


def test_import_page_post_with_ibom(client, tmp_path):
    from tests.test_ibom_parser import PAYLOAD
    body = (
        "<html><script>var pcbdata = JSON.parse(LZString.decompressFromBase64("
        f'"{PAYLOAD}"));</script></html>'
    )
    data = {
        "brand": "Test",
        "model": "WEB-IBOM",
        "manufacturer": "M",
        "bom_file": (io.BytesIO(body.encode("utf-8")), "board_ibom.html"),
    }
    resp = client.post("/import", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302
    assert "/device/" in resp.headers["Location"]


def test_import_page_rejects_bad_html(client):
    data = {
        "brand": "Test",
        "model": "WEB-BAD",
        "manufacturer": "M",
        "bom_file": (io.BytesIO(b"<html>nothing</html>"), "bad.html"),
    }
    resp = client.post("/import", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_materials_page_empty(client):
    resp = client.get("/materials")
    assert resp.status_code == 200
    assert b"Nessun materiale" in resp.data


def test_materials_page_shows_material_and_link(client, tmp_path):
    db_url = f"sqlite:///{tmp_path / 'mat.db'}"
    from ariadne.config import AppConfig, DatabaseConfig
    config = AppConfig(database=DatabaseConfig(url=db_url), mongo=MongoConfig(
        uri="mongodb://localhost:27017", database="ariadne_raw", collection="bom_files", from_env=True))
    db = Database(config.database)
    did = db.find_or_create_device(Device(brand="Test", model_name="MAT-DEV", manufacturer="M"))
    eid = db.insert_bom_entry(did, BOMEntry(item_number=1, quantity=1, reference_designator="C1",
                                            part_value="2u2-GRM188R61E225MA12D", mounting_type="SMT"))
    from ariadne.models import Material
    mid = db.insert_material(Material(material_name="Barium titanate", casrn="12047-27-7", category="element"))
    db.link_material(eid, mid, mass_mg=4.48, note="MLCC", source_mdf="class_d.xml")
    db.close()

    app2 = create_app(config)
    app2.config["TESTING"] = True
    resp = app2.test_client().get("/materials")
    assert resp.status_code == 200
    assert b"Barium titanate" in resp.data
    assert b"12047-27-7" in resp.data
    assert b"GRM188R61E225MA12D" in resp.data


def test_mdf_import_page_get(client):
    resp = client.get("/mdf-import")
    assert resp.status_code == 200
    assert b"Import MDF" in resp.data


def test_mdf_import_post_rejects_bad_ext(client):
    resp = client.post("/mdf-import", data={"mdf_file": (io.BytesIO(b"x"), "foo.txt")},
                       content_type="multipart/form-data")
    assert resp.status_code == 302
    assert "/mdf-import" in resp.headers["Location"]


def test_mdf_import_post_xml_linkless(client):
    xml = (
        '<MainDeclaration xmlns="http://webstds.ipc.org/175x/2.0" version="2.0">'
        '<Product unitType="Each"><ProductID itemNumber="GRM188R61E225MA12D"/>'
        '<MaterialInfo><HomogeneousMaterialList>'
        '<HomogeneousMaterial name="Ceramic" materialGroupName="Ceramic">'
        '<Amount value="5.2" UOM="mg"/>'
        '<SubstanceCategoryList><SubstanceCategory name="Supplier">'
        '<Substance name="Barium titanate"><SubstanceID identity="12047-27-7" authority="CAS"/>'
        '<Concentration value="86.27"/></Substance>'
        '</SubstanceCategory></SubstanceCategoryList></HomogeneousMaterial>'
        '</HomogeneousMaterialList></MaterialInfo></Product></MainDeclaration>'
    )
    resp = client.post("/mdf-import",
                       data={"mdf_file": (io.BytesIO(xml.encode("utf-8")), "class_d.xml")},
                       content_type="multipart/form-data")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/materials")
    # il materiale è stato creato e compare nella pagina materiali
    resp2 = client.get("/materials")
    assert b"Barium titanate" in resp2.data


def test_mdf_import_post_pdf_ingests(client):
    zvei = FIXTURES / "mdf_zvei_mlcc_example.pdf"
    with open(zvei, "rb") as f:
        resp = client.post(
            "/mdf-import",
            data={"mdf_file": (f, zvei.name)},
            content_type="multipart/form-data",
        )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/materials")
    resp2 = client.get("/materials")
    # 4 sostanze dichiarate dal PDF ZVEI (barium, nickel, copper, tin)
    assert b"barium" in resp2.data
    assert b"nickel" in resp2.data
    assert b"7440-02-0" in resp2.data
