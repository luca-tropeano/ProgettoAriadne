from __future__ import annotations

from click.testing import CliRunner

from ariadne.main import cli


def _runner():
    return CliRunner()


def test_process_csv_success(tmp_path, monkeypatch):
    csv = tmp_path / "bom.csv"
    csv.write_text("Ref,Qty,Value,Footprint\nR1,1,10k,0603\nC1,2,100nF,0402\n", encoding="utf-8")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'a.db'}")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")

    result = _runner().invoke(
        cli, ["process", str(csv), "--brand", "Test", "--model", "M1"]
    )
    assert result.exit_code == 0
    assert "Imported:" in result.output
    assert "2" in result.output


def test_process_unsupported_format_exit_1(tmp_path, monkeypatch):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'b.db'}")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")

    result = _runner().invoke(cli, ["process", str(f), "--brand", "Test", "--model", "M1"])
    assert result.exit_code == 1
    assert "Unsupported format" in result.output


def test_process_missing_file_exit_2(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")
    result = _runner().invoke(cli, ["process", "does_not_exist.csv"])
    assert result.exit_code == 2


def test_stats_command(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'c.db'}")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")
    result = _runner().invoke(cli, ["stats"])
    assert result.exit_code == 0
    assert "Devices:" in result.output
    assert "BOM Entries:" in result.output
    assert "Raw docs (MongoDB):" in result.output


def test_process_pdf_with_no_text(monkeypatch, tmp_path):
    pdf = tmp_path / "empty.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'd.db'}")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")
    result = _runner().invoke(cli, ["process", str(pdf), "--brand", "T", "--model", "M"])
    assert result.exit_code == 1


def test_strapi_sync_requires_token(monkeypatch, tmp_path):
    monkeypatch.delenv("STRAPI_API_TOKEN", raising=False)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'e.db'}")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")
    result = _runner().invoke(cli, ["strapi-sync"])
    assert result.exit_code == 1
    assert "STRAPI_API_TOKEN" in result.output


def test_strapi_sync_pushes_devices(monkeypatch, tmp_path):
    import ariadne.strapi_client as sc

    monkeypatch.setenv("STRAPI_API_TOKEN", "fake-token")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'f.db'}")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")

    # seed device
    from ariadne.config import AppConfig
    from ariadne.database import Database
    from ariadne.models import BOMEntry, Device

    cfg = AppConfig.from_env()
    db = Database(cfg.database)
    did = db.find_or_create_device(Device(brand="B", model_name="SYNC-MODEL", manufacturer="M"))
    db.insert_bom_entry(did, BOMEntry(item_number=1, quantity=1, reference_designator="R1",
                                      mounting_type="SMT"))
    db.close()

    def _fake_init(self, *a, **k):
        pass

    monkeypatch.setattr(sc.StrapiClient, "__init__", _fake_init)
    monkeypatch.setattr(
        sc.StrapiClient,
        "sync_device",
        lambda self, device, entries: {"device_id": 1, "entries_pushed": len(entries)},
    )
    monkeypatch.setattr(sc.StrapiClient, "close", lambda self: None)

    result = _runner().invoke(cli, ["strapi-sync"])
    assert result.exit_code == 0
    assert "SYNC-MODEL" in result.output


def test_mdf_ingest_json(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'g.db'}")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")
    mdf = tmp_path / "mdf.json"
    mdf.write_text(
        '{"materials": [{"material_name": "Copper", "casrn": "7440-50-8", '
        '"category": "element"}]}',
        encoding="utf-8",
    )
    result = _runner().invoke(cli, ["mdf-ingest", str(mdf)])
    assert result.exit_code == 0
    assert "Materiali creati:" in result.output
    assert "1" in result.output


def test_mdf_ingest_xml(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'i.db'}")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")
    mdf = tmp_path / "mdf.xml"
    mdf.write_text(
        '<MainDeclaration xmlns="http://webstds.ipc.org/175x/2.0" version="2.0">'
        '<Product unitType="Each"><ProductID itemNumber="GRM188R61E225MA12D"/>'
        '<MaterialInfo><HomogeneousMaterialList>'
        '<HomogeneousMaterial name="Ceramic" materialGroupName="Ceramic">'
        '<Amount value="5.2" UOM="mg"/>'
        '<SubstanceCategoryList><SubstanceCategoryListID identity="JIG101-3" authority="JIG" revision="3.0"/>'
        '<SubstanceCategory name="Supplier">'
        '<Substance name="Barium titanate"><SubstanceID identity="12047-27-7" authority="CAS"/>'
        '<Concentration value="86.27"/></Substance>'
        '</SubstanceCategory></SubstanceCategoryList></HomogeneousMaterial>'
        '</HomogeneousMaterialList></MaterialInfo></Product></MainDeclaration>',
        encoding="utf-8",
    )
    result = _runner().invoke(cli, ["mdf-ingest", str(mdf)])
    assert result.exit_code == 0
    assert "MDF ingestione (XML (IPC-1752A/B class D)):" in result.output
    assert "Materiali creati:     1" in result.output


def test_mdf_ingest_pdf_parses_real_fixture(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'h.db'}")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")
    from pathlib import Path
    pdf = Path(__file__).resolve().parent.parent / "test_data" / "mdf_zvei_mlcc_example.pdf"
    result = _runner().invoke(cli, ["mdf-ingest", str(pdf)])
    assert result.exit_code == 0
    assert "MDF ingestione (PDF (Material Declaration, pdfplumber)):" in result.output
    assert "Materiali creati:     4" in result.output
    assert "[WARN] Nessun part number" in result.output


def test_mdf_download_unknown_source_reports_error(tmp_path, monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")
    result = _runner().invoke(
        cli,
        ["mdf-download", "GRM188R61E225MA12D", "--source", "nope", "--out-dir", str(tmp_path)],
    )
    assert result.exit_code == 1
    assert "source sconosciuto" in result.output


def test_strapi_sync_materials(monkeypatch, tmp_path):
    import ariadne.strapi_client as sc

    monkeypatch.setenv("STRAPI_API_TOKEN", "fake-token")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'materials.db'}")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")

    from ariadne.config import AppConfig
    from ariadne.database import Database
    from ariadne.models import BOMEntry, Device, Material

    db = Database(AppConfig.from_env().database)
    did = db.find_or_create_device(Device(brand="B", model_name="MAT-SYNC", manufacturer="M"))
    eid = db.insert_bom_entry(did, BOMEntry(item_number=1, quantity=1, reference_designator="R1",
                                            mounting_type="SMT"))
    mid = db.insert_material(Material(material_name="Copper", casrn="7440-50-8", category="element"))
    db.link_material(eid, mid, mass_mg=1.5, note="x", source_mdf="mdf.xml")
    db.close()

    calls = {}

    def _fake_init(self, *a, **k):
        pass

    def _push(self, entry_sid, material_sid, mass_mg, note=None, source_mdf=None):
        calls["entry_sid"] = entry_sid
        calls["material_sid"] = material_sid
        calls["mass_mg"] = mass_mg
        calls["source_mdf"] = source_mdf
        return 9

    monkeypatch.setattr(sc.StrapiClient, "__init__", _fake_init)
    monkeypatch.setattr(
        sc.StrapiClient,
        "sync_device",
        lambda self, device, entries: {
            "device_id": 1,
            "entries_pushed": len(entries),
            "entry_strapi_ids": [1] * len(entries),
        },
    )
    monkeypatch.setattr(sc.StrapiClient, "upsert_material", lambda self, m: 5)
    monkeypatch.setattr(sc.StrapiClient, "push_component_material", _push)
    monkeypatch.setattr(sc.StrapiClient, "close", lambda self: None)

    result = _runner().invoke(cli, ["strapi-sync", "--materials"])
    assert result.exit_code == 0
    assert "MAT-SYNC" in result.output
    assert "materials: 1 link sincronizzati" in result.output
    assert calls["entry_sid"] == 1
    assert calls["material_sid"] == 5
    assert calls["mass_mg"] == 1.5
    assert calls["source_mdf"] == "mdf.xml"