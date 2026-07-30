from ariadne.pdf_parser import parse_pdf_bom_text


def test_simple_bom_lines():
    text = """1 14 C1,C5,C7,C8,C9 100nF 0603 KEMET
2 1 C2 22uF L8.3 PANASONIC
3 1 D1 STPS0560Z SOD123 STMICROELECTRONICS"""
    entries = parse_pdf_bom_text(text)
    assert len(entries) == 3
    assert entries[0].item_number == 1
    assert entries[0].quantity == 14
    assert "C1" in entries[0].reference_designator
    assert entries[0].part_value == "100nF"


def test_line_with_x_quantity():
    text = "14x C1,C5,C7 100nF 0603 KEMET"
    entries = parse_pdf_bom_text(text)
    assert len(entries) >= 1
    assert entries[0].quantity == 14


def test_designator_only_line():
    text = "R1 10k 0603"
    entries = parse_pdf_bom_text(text)
    assert len(entries) >= 1
    assert entries[0].reference_designator == "R1"


def test_empty_text():
    assert parse_pdf_bom_text("") == []


def test_no_designators():
    text = "Some random text without any component references"
    assert parse_pdf_bom_text(text) == []


def test_multiple_designators_same_line():
    text = "10 C1 C2 C3 100nF 0603"
    entries = parse_pdf_bom_text(text)
    assert len(entries) >= 1
    assert "C1" in entries[0].reference_designator
    assert "C2" in entries[0].reference_designator


def test_page_separators():
    text = """--- Page 1 ---
1 5 R1,R2 10k 0603
2 3 C1 100nF 0603

--- Page 2 ---
3 1 U1 STM32F103 LQFP48 STMICROELECTRONICS"""
    entries = parse_pdf_bom_text(text)
    assert len(entries) == 3


def test_tht_detection():
    text = "1 2 U1 MC68000 DIP-64"
    entries = parse_pdf_bom_text(text)
    assert len(entries) >= 1
    assert entries[0].mounting_type == "THT"


def test_manufacturer_detection():
    text = "1 1 U4 STM32F103CBT6 STMICROELECTRONICS"
    entries = parse_pdf_bom_text(text)
    assert len(entries) >= 1
    assert entries[0].manufacturer == "STMICROELECTRONICS"


def test_real_bom_sample():
    text = """Item Qty Reference Part Value Package Manufacturer
1 14 C1,C5,C7,C8,C9,C11,C20,C26,C27,C28,C29,C33,C34,C37 100 nF 0603 KEMET
2 1 C2 22 uF L8.3_W8.3_H9.5 PANASONIC
21 1 D1 STPS0560Z SOD123 STMICROELECTRONICS
70 1 U1 STSPIN32F0B VFQFPN48 STMICROELECTRONICS"""
    entries = parse_pdf_bom_text(text)
    assert len(entries) == 4
    assert entries[0].part_value is not None
    assert entries[0].manufacturer == "KEMET"
