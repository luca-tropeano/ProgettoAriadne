from ariadne.models import BOMEntry, Device, ImportResult


def test_bom_entry_defaults():
    e = BOMEntry(item_number=1, quantity=5, reference_designator="R1,R2")
    assert e.mounting_type == "SMT"
    assert e.part_value is None


def test_bom_entry_full():
    e = BOMEntry(
        item_number=10, quantity=14,
        reference_designator="C1,C5,C7",
        part_value="100 nF",
        package="0603",
        manufacturer="KEMET",
        mounting_type="SMT",
    )
    assert e.manufacturer == "KEMET"
    assert e.quantity == 14


def test_device_defaults():
    d = Device(model_name="TEST-001")
    assert d.brand == ""
    assert d.year_of_production is None


def test_import_result_success():
    r = ImportResult(total_rows=10, imported_rows=10, failed_rows=0)
    assert r.success is True


def test_import_result_failure():
    r = ImportResult(total_rows=10, imported_rows=8, failed_rows=2)
    assert r.success is False
