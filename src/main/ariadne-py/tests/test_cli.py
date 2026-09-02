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