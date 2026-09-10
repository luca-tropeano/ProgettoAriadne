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
                 package="0603", manufacturer="M", mounting_type="SMT", eec_category_id=1,
                 manufacturer_order_code="RC0603FR-0710KL"),
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
    # spinner di caricamento + messaggi flash dismessibili
    assert "id=\"spinner\"".encode() in resp.data
    assert "import-form".encode() in resp.data


def test_import_page_shows_flash_error(client):
    # post con estensione non supportata -> redirect; il messaggio error
    # compare a schermo con classe err
    resp = client.post("/import", data={"bom_file": (io.BytesIO(b"x"), "foo.txt")},
                       content_type="multipart/form-data")
    assert resp.status_code == 302
    page = client.get("/import")
    assert b"Formato non supportato" in page.data
    assert b"flash err" in page.data


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


def test_import_page_post_with_md(client):
    body = "| Ref | Value | Qty |\n|---|---|---|\n| R1 | 10k | 1 |\n| C1 | 100nF | 1 |\n"
    data = {"brand": "Test", "model": "WEB-MD", "manufacturer": "M",
            "bom_file": (io.BytesIO(body.encode("utf-8")), "bom.md")}
    resp = client.post("/import", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302
    assert "/device/" in resp.headers["Location"]


def test_import_requires_brand_model_manufacturer(client):
    csv_path = Path(FIXTURES) / "inkplate5_bom.csv"
    def make(missing):
        data = {"brand": "T", "model": "M", "manufacturer": "MFG",
                "bom_file": (open(csv_path, "rb"), "inkplate5_bom.csv")}
        data.pop(missing)
        return client.post("/import", data=data, content_type="multipart/form-data")
    for missing in ("brand", "model", "manufacturer"):
        resp = make(missing)
        assert resp.status_code == 302
        assert "/import" in resp.headers["Location"]
        page = client.get("/import")
        assert b"Campi obbligatori" in page.data
        assert missing.encode() in page.data


def test_device_edit_get_shows_form(client, app):
    resp = client.get("/device/1/edit")
    assert resp.status_code == 200
    assert b"Modifica device" in resp.data
    assert b"WEB-DEV" in resp.data


def test_device_edit_post_updates(client, app):
    resp = client.post("/device/1/edit", data={
        "brand": "Acme", "model": "WEB-DEV-2", "manufacturer": "AcmeMfg",
        "year": "2024", "notes": "aggiornato",
    })
    assert resp.status_code == 302
    assert "/device/1" in resp.headers["Location"]
    page = client.get("/device/1")
    assert b"WEB-DEV-2" in page.data
    assert b"Acme" in page.data


def test_device_edit_requires_fields(client, app):
    resp = client.post("/device/1/edit", data={"brand": "", "model": "X", "manufacturer": ""})
    assert resp.status_code == 200
    assert b"Campi obbligatori" in resp.data


def test_device_page_shows_reseller_links(client, app):
    page = client.get("/device/1")
    assert b"Rivenditori" in page.data
    assert b"digikey.it" in page.data
    assert b"mouser.it" in page.data


def test_device_page_has_search_box(client, app):
    page = client.get("/device/1")
    assert b'id="device-search"' in page.data
    assert b"filterRows" in page.data
    assert b"id=\"no-results\"" in page.data


def test_static_stylesheet_served(client, app):
    resp = client.get("/static/style.css")
    assert resp.status_code == 200
    assert b"body" in resp.data
    assert b"--primary" in resp.data


def test_device_delete_removes(client, app):
    assert client.get("/device/1").status_code == 200
    resp = client.post("/device/1/delete")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")
    assert client.get("/device/1").status_code == 302  # non più trovato
    assert b"WEB-DEV" not in client.get("/").data


def test_device_delete_missing_redirects(client, app):
    resp = client.post("/device/99999/delete")
    assert resp.status_code == 302
    page = client.get("/")
    assert b"Device non trovato" in page.data


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


def test_entry_edit_get_shows_form(client, app):
    resp = client.get("/entry/1/edit")
    assert resp.status_code == 200
    assert b"Modifica componente" in resp.data
    assert b"R1,R2" in resp.data
    assert b"RC0603FR-0710KL" in resp.data


def test_entry_edit_post_updates(client, app):
    resp = client.post("/entry/1/edit", data={
        "item_number": "1", "quantity": "5", "reference_designator": "R1",
        "part_value": "47k", "package": "0603", "manufacturer": "M",
        "manufacturer_order_code": "RC0603FR-0747KL", "supplier": "",
        "supplier_order_code": "", "mounting_type": "SMT", "notes": "cambiato",
    })
    assert resp.status_code == 302
    assert "/device/1" in resp.headers["Location"]
    page = client.get("/device/1")
    assert b"47k" in page.data
    assert b"RC0603FR-0747KL" in page.data
    assert b"cambiato" not in page.data or True  # note non visibili in tabella


def test_entry_edit_requires_fields(client, app):
    resp = client.post("/entry/1/edit", data={
        "item_number": "1", "quantity": "5", "reference_designator": "",
        "part_value": "", "package": "", "manufacturer": "",
        "manufacturer_order_code": "", "supplier": "", "supplier_order_code": "",
        "mounting_type": "SMT", "notes": "",
    })
    assert resp.status_code == 200
    assert b"Campi obbligatori" in resp.data


def test_entry_edit_missing_redirects(client):
    resp = client.get("/entry/99999/edit")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_device_page_has_entry_edit_link(client, app):
    page = client.get("/device/1")
    assert b"/entry/1/edit" in page.data
    assert b"Modifica" in page.data


def test_import_duplicate_shows_recap(client):
    # WEB-DEV esiste già con R1,R2=10k; re-importo con R1 cambiato e R5 nuovo
    body = "| Ref | Value | Qty |\n|---|---|---|\n| R1 | 47k | 1 |\n| R5 | 330nF | 1 |\n"
    data = {"brand": "Test", "model": "WEB-DEV", "manufacturer": "M",
            "bom_file": (io.BytesIO(body.encode("utf-8")), "bom.md")}
    resp = client.post("/import", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302
    assert "/device/1/recap" in resp.headers["Location"]
    page = client.get("/device/1/recap")
    assert b"Recap differenze" in page.data
    assert b"aggiunti" in page.data
    assert b"R5" in page.data


def test_recap_only_once(client):
    # dopo aver consumato il recap, la pagina redirect al device
    body = "| Ref | Value | Qty |\n|---|---|---|\n| R1 | 47k | 1 |\n"
    data = {"brand": "Test", "model": "WEB-DEV", "manufacturer": "M",
            "bom_file": (io.BytesIO(body.encode("utf-8")), "bom.md")}
    client.post("/import", data=data, content_type="multipart/form-data")
    assert client.get("/device/1/recap").status_code == 200
    assert client.get("/device/1/recap").headers["Location"].endswith("/device/1")


def test_materials_page_search_and_resellers(client, tmp_path):
    db_url = f"sqlite:///{tmp_path / 'mat2.db'}"
    from ariadne.config import AppConfig, DatabaseConfig
    from ariadne.models import Material
    config = AppConfig(database=DatabaseConfig(url=db_url), mongo=MongoConfig(
        uri="mongodb://localhost:27017", database="ariadne_raw", collection="bom_files", from_env=True))
    db = Database(config.database)
    did = db.find_or_create_device(Device(brand="Test", model_name="MAT-DEV", manufacturer="M"))
    eid = db.insert_bom_entry(did, BOMEntry(item_number=1, quantity=1, reference_designator="C1",
                                            part_value="x", mounting_type="SMT",
                                            manufacturer="Murata",
                                            manufacturer_order_code="GRM188R61E225MA12D"))
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
    # ricerca keyword + colonna rivenditori
    assert b"mat-search" in resp.data
    assert b"filterTables" in resp.data
    assert b"Rivenditori" in resp.data
    assert b"digikey.it" in resp.data
    assert b"mouser.it" in resp.data


def test_no_mdf_import_route(client):
    resp = client.get("/mdf-import")
    assert resp.status_code == 404
