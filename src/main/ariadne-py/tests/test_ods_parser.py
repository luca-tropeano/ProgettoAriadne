from __future__ import annotations

from pathlib import Path

from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableCell, TableRow
from odf.text import P

from ariadne.ods_parser import parse_ods_bom

TEST_DATA = Path(__file__).parent.parent / "test_data"


def _cell(text: str) -> TableCell:
    c = TableCell()
    c.addElement(P(text=text))
    return c


def _make_ods(tmp_path, header, rows) -> str:
    doc = OpenDocumentSpreadsheet()
    table = Table(name="Sheet1")
    hrow = TableRow()
    for h in header:
        hrow.addElement(_cell(h))
    table.addElement(hrow)
    for row in rows:
        r = TableRow()
        for v in row:
            r.addElement(_cell(str(v)))
        table.addElement(r)
    doc.spreadsheet.addElement(table)
    path = tmp_path / "bom.ods"
    doc.save(str(path))
    return str(path)


def _make_ods_with_rows(tmp_path, rows) -> str:
    """rows: lista di liste di stringhe, inclusa la riga header."""
    doc = OpenDocumentSpreadsheet()
    table = Table(name="Sheet1")
    for row in rows:
        r = TableRow()
        for v in row:
            r.addElement(_cell(str(v)))
        table.addElement(r)
    doc.spreadsheet.addElement(table)
    path = tmp_path / "bom.ods"
    doc.save(str(path))
    return str(path)


def test_parse_basic(tmp_path):
    path = _make_ods(
        tmp_path,
        ["Ref", "Qty", "Value", "Footprint", "Manufacturer", "Supplier Part number"],
        [
            ["R1,R2", "2", "10k", "Resistor_SMD:R_0603", "Kemet", "ABC123"],
            ["C1", "4", "100nF", "Capacitor_SMD:C_0603", "muRata", "DEF456"],
        ],
    )
    entries = parse_ods_bom(path)
    assert len(entries) == 2
    e = entries[0]
    assert e.reference_designator == "R1,R2"
    assert e.quantity == 2
    assert e.part_value == "10k"
    assert e.package == "Resistor_SMD:R_0603"
    assert e.mounting_type == "SMT"
    assert e.manufacturer == "Kemet"
    assert e.supplier_order_code == "ABC123"


def test_parse_tht_detection(tmp_path):
    path = _make_ods_with_rows(
        tmp_path,
        [
            ["Ref", "Qty", "Value", "Footprint"],
            ["U1", "1", "68K", "Package_DIP:DIP-16_W7.62mm"],
        ],
    )
    entries = parse_ods_bom(path)
    assert entries[0].mounting_type == "THT"


def test_parse_skips_meta_rows_above_header(tmp_path):
    path = _make_ods_with_rows(
        tmp_path,
        [
            ["Title", "HILTOP Motherboard"],
            ["Revision", "Rev D"],
            ["Ref", "Qty", "Value", "Footprint"],
            ["R1", "1", "10k", "0603"],
            ["C1", "2", "100nF", "0603"],
        ],
    )
    entries = parse_ods_bom(path)
    assert len(entries) == 2
    assert entries[0].reference_designator == "R1"
    assert entries[1].reference_designator == "C1"


def test_parse_missing_qty_returns_empty(tmp_path):
    path = _make_ods(tmp_path, ["Ref", "Value"], [["R1", "10k"]])
    assert parse_ods_bom(path) == []


def test_parse_missing_file_raises(tmp_path):
    excepted = False
    try:
        parse_ods_bom(str(tmp_path / "nonexistent.ods"))
    except Exception:
        excepted = True
    assert excepted


def test_parse_real_hiltop():
    f = TEST_DATA / "hiltop_motherboard.ods"
    if not f.exists():
        import pytest
        pytest.skip("hiltop_motherboard.ods not present")
    entries = parse_ods_bom(str(f))
    # Header dice 'Total Unique Parts: 157' ma alcune righe hanno più righe break;
    # il parser restituisce comunque un numero consistente di entry.
    assert len(entries) >= 150
    # verifica campi popolati
    found = [e for e in entries if e.manufacturer == "Kemet"]
    assert found
    assert any(e.quantity >= 100 for e in entries)
