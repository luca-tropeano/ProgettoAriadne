from ariadne.md_parser import parse_md_bom


def test_parse_expands_designator_ranges(tmp_path):
    p = tmp_path / "bom.md"
    p.write_text(
        "| Item | Description | Part Number | Manufacturer | Qty | Notes |\n"
        "|------|-------------|-------------|--------------|-----|-------|\n"
        "| C1-C10 | Polymer Cap | 25ZLH470M | Rubycon | 10 | Bulk |\n"
        "| U10-U25 | Power Stage | TDA21490 | Infineon | 16 | DrMOS |\n"
        "| L17-L20 | Inductor | IHLP-5050CE-01 | Vishay | 4 | VCCIN |\n",
        encoding="utf-8",
    )
    entries = parse_md_bom(str(p))
    assert len(entries) == 3
    assert entries[0].reference_designator == (
        "C1,C2,C3,C4,C5,C6,C7,C8,C9,C10"
    )
    assert entries[0].quantity == 10
    assert entries[0].manufacturer == "Rubycon"
    assert entries[0].manufacturer_order_code == "25ZLH470M"
    assert entries[1].reference_designator == (
        "U10,U11,U12,U13,U14,U15,U16,U17,U18,U19,U20,U21,U22,U23,U24,U25"
    )
    assert entries[1].quantity == 16
    assert entries[2].reference_designator == "L17,L18,L19,L20"


def test_parse_skips_dash_only_ref_rows(tmp_path):
    p = tmp_path / "bom.md"
    p.write_text(
        "| Item | Description | Qty |\n"
        "|------|-------------|-----|\n"
        "| U1 | MCU | 1 |\n"
        "| - | Mounting holes | 5 |\n"
        "| R1 | 10k | 2 |\n"
        "| - | Standoffs | 10 |\n",
        encoding="utf-8",
    )
    entries = parse_md_bom(str(p))
    assert len(entries) == 2
    assert [e.reference_designator for e in entries] == ["U1", "R1"]


def test_parse_qty_range_uses_first_number(tmp_path):
    p = tmp_path / "bom.md"
    p.write_text(
        "| Ref | Description | Qty |\n"
        "|-----|-------------|-----|\n"
        "| J100 | PCIe x16 | 1-2 |\n"
        "| J101-J103 | PCIe x1 | 3 |\n",
        encoding="utf-8",
    )
    entries = parse_md_bom(str(p))
    assert entries[0].quantity == 1
    assert entries[1].quantity == 3


def test_parse_simple_markdown_table(tmp_path):
    p = tmp_path / "bom.md"
    p.write_text(
        "# BOM Board\n\n"
        "Some intro text that is not a table.\n\n"
        "| Ref | Value | Qty | Footprint | Manufacturer | MPN |\n"
        "|-----|-------|-----|-----------|--------------|-----|\n"
        "| C1, C2 | **100nF** | 2 | 0603 | KEMET | C0603C104K5RACTU |\n"
        "| R1 | 10k | 1 | 0603 | YAGEO | RC0603JR-070RL |\n",
        encoding="utf-8",
    )
    entries = parse_md_bom(str(p))
    assert len(entries) == 2

    c = entries[0]
    assert c.reference_designator == "C1,C2"
    assert c.quantity == 2
    assert c.part_value == "100nF"
    assert c.package == "0603"
    assert c.manufacturer == "KEMET"
    assert c.manufacturer_order_code == "C0603C104K5RACTU"
    assert c.mounting_type == "SMT"
    assert c.item_number == 1

    r = entries[1]
    assert r.reference_designator == "R1"
    assert r.part_value == "10k"
    assert r.manufacturer_order_code == "RC0603JR-070RL"


def test_parse_row_without_qty_defaults_to_count(tmp_path):
    p = tmp_path / "bom.md"
    p.write_text(
        "| Ref | Value | Footprint |\n"
        "|---|---|---|\n"
        "| U1 | 3.3V LDO | SOT-23 |\n",
        encoding="utf-8",
    )
    entries = parse_md_bom(str(p))
    assert len(entries) == 1
    assert entries[0].quantity == 1
    assert entries[0].package == "SOT-23"
    assert entries[0].mounting_type == "SMT"


def test_parse_dnp_flag_and_italic_value(tmp_path):
    p = tmp_path / "bom.md"
    p.write_text(
        "| Ref | Value | Qty | DNP |\n"
        "|---|---|---|---|\n"
        "| *DNP* | 47uF | 1 | yes |\n",
        encoding="utf-8",
    )
    entries = parse_md_bom(str(p))
    assert len(entries) == 1
    assert entries[0].reference_designator == "DNP"
    assert entries[0].part_value == "47uF"
    assert entries[0].notes == "DNP"


def test_parse_multiple_tables_and_ignore_non_table(tmp_path):
    p = tmp_path / "bom.md"
    p.write_text(
        "```\nnot a table\n```\n\n"
        "| Ref | Value | Qty |\n"
        "|---|---|---|\n"
        "| R1 | 10k | 2 |\n\n"
        "Text between tables.\n\n"
        "| Ref | Value |\n"
        "|---|---|\n"
        "| C1 | 100nF |\n",
        encoding="utf-8",
    )
    entries = parse_md_bom(str(p))
    assert len(entries) == 2
    assert entries[0].reference_designator == "R1"
    assert entries[1].reference_designator == "C1"


def test_parse_ignores_table_without_ref_column(tmp_path):
    p = tmp_path / "bom.md"
    p.write_text(
        "| Notes | Text |\n"
        "|---|---|\n"
        "| hello | world |\n",
        encoding="utf-8",
    )
    assert parse_md_bom(str(p)) == []


def test_parse_empty_file(tmp_path):
    p = tmp_path / "empty.md"
    p.write_text("# nothing here\n", encoding="utf-8")
    assert parse_md_bom(str(p)) == []