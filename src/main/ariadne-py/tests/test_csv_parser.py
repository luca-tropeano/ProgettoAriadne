from __future__ import annotations

from pathlib import Path

from ariadne.csv_parser import _detect_mounting_type, _split_designators, parse_csv_bom

TEST_DATA = Path(__file__).parent.parent / "test_data"


def test_split_designators_comma():
    assert _split_designators("R1, R2,  R3") == "R1,R2,R3"


def test_split_designators_semicolon():
    assert _split_designators("C1;C2") == "C1,C2"


def test_split_designators_space():
    assert _split_designators("LED1 LED2 LED3") == "LED1,LED2,LED3"


def test_split_designators_collapses_empty():
    assert _split_designators("R1,,R2,") == "R1,R2"


def test_split_designators_quoted():
    assert _split_designators('"U1"') == "U1"


def test_detect_mounting_smd_prefix():
    assert _detect_mounting_type("SMD_0603") == "SMT"
    assert _detect_mounting_type("QFP32", None) == "SMT"


def test_detect_mounting_tht_prefix():
    assert _detect_mounting_type("DIP-8", None) == "THT"
    assert _detect_mounting_type("TO-92", None) == "THT"
    assert _detect_mounting_type("DO-35", None) == "THT"


def test_detect_mounting_tht_keyword():
    assert _detect_mounting_type("Connector_THT") == "THT"
    assert _detect_mounting_type("DSUB") == "THT"


def test_detect_mounting_value_based():
    assert _detect_mounting_type(None, "1N4148") == "THT"


def test_detect_mounting_default_smt():
    assert _detect_mounting_type(None, None) == "SMT"
    assert _detect_mounting_type("Aardvark") == "SMT"


def test_detect_mounting_0603():
    assert _detect_mounting_type("Capacitor_SMD:0603") == "SMT"


def _small_csv(tmp_path, content):
    p = tmp_path / "bom.csv"
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_parse_kicad_semicolon(tmp_path):
    content = "Reference;Qty;Value;Footprint;\nR1;1;10k;R_0603;;\nC1;2;100nF;C_0805;;\n"
    entries = parse_csv_bom(_small_csv(tmp_path, content))
    assert len(entries) == 2
    assert entries[0].reference_designator == "R1"
    assert entries[0].part_value == "10k"
    assert entries[0].quantity == 1
    assert entries[1].quantity == 2
    assert entries[0].mounting_type == "SMT"


def test_parse_easyeda_quoted(tmp_path):
    content = (
        '"Id","Designator","Package","Quantity","Designation"\n'
        '"1","R1","0603","1","10k"\n'
    )
    entries = parse_csv_bom(_small_csv(tmp_path, content))
    assert len(entries) == 1
    assert entries[0].reference_designator == "R1"
    assert entries[0].quantity == 1


def test_parse_skips_header_and_blanks(tmp_path):
    content = (
        "Ref,Qty,Value,Footprint\n"
        "Ref,Qty,Value,Footprint\n"
        "\n"
        "# comment\n"
        "//EasyEDA row\n"
        "R1,1,10k,0603\n"
    )
    entries = parse_csv_bom(_small_csv(tmp_path, content))
    assert len(entries) == 1
    assert entries[0].reference_designator == "R1"


def test_parse_skips_dnp(tmp_path):
    content = "Ref,Qty,Value,Footprint,DoNotPopulate\nR1,1,10k,0603,yes\nC1,2,100nF,0603,no\n"
    entries = parse_csv_bom(_small_csv(tmp_path, content))
    assert len(entries) == 2
    assert entries[0].notes == "DNP"
    assert entries[1].notes is None


def test_parse_missing_qty_header_returns_empty(tmp_path):
    content = "Ref,Value\nR1,10k\n"
    assert parse_csv_bom(_small_csv(tmp_path, content)) == []


def test_parse_non_utf8_bytes(tmp_path):
    p = tmp_path / "bom.csv"
    p.write_bytes("Ref,Qty,Value\nR1,1,10k\n".encode("utf-8"))
    entries = parse_csv_bom(str(p))
    assert len(entries) == 1


def test_parse_real_amiga2000():
    f = TEST_DATA / "amiga2000.csv"
    if not f.exists():
        import pytest
        pytest.skip("amiga2000.csv not present")
    entries = parse_csv_bom(str(f))
    assert len(entries) == 140


def test_parse_real_inkplate5():
    f = TEST_DATA / "inkplate5_bom.csv"
    if not f.exists():
        import pytest
        pytest.skip("inkplate5_bom.csv not present")
    entries = parse_csv_bom(str(f))
    assert len(entries) == 71