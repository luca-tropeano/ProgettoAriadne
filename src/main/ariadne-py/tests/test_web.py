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