from ariadne.bom_diff import diff_boms


def _row(ref, value, qty=1, mfr=None, mpn=None, pkg=None):
    return {
        "reference_designator": ref,
        "part_value": value,
        "quantity": qty,
        "manufacturer": mfr,
        "manufacturer_order_code": mpn,
        "package": pkg,
    }


def test_diff_identical():
    d = diff_boms([_row("R1,R2", "10k")], [_row("R1,R2", "10k")])
    assert not d.has_changes


def test_diff_added_and_removed():
    d = diff_boms([_row("R1,R2", "10k")], [_row("R1,R5", "10k")])
    assert d.added == ["R5"]
    assert d.removed == ["R2"]
    assert d.modified == []


def test_diff_modified_value():
    d = diff_boms([_row("R1", "10k", pkg="0603")], [_row("R1", "47k", pkg="0603")])
    assert d.added == []
    assert d.removed == []
    assert len(d.modified) == 1
    assert d.modified[0]["ref"] == "R1"
    assert d.modified[0]["old"]["part_value"] == "10k"
    assert d.modified[0]["new"]["part_value"] == "47k"


def test_diff_range_already_expanded():
    # nel DB i range ("C1-C10") arrivano già espansi dai parser, con la qty della riga
    old = [_row("C1,C2,C3", "100nF", qty=3)]
    new = [_row(f"C{i}", "100nF", qty=3) for i in range(1, 4)]
    d = diff_boms(old, new)
    assert not d.has_changes


def test_diff_expand_multivalue_refs():
    old = [_row("R1,R2", "10k")]
    new = [_row("R1", "10k"), _row("R2", "10k")]
    assert not diff_boms(old, new).has_changes