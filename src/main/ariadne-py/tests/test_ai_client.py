from ariadne.ai_client import _parse_response
from ariadne.models import BOMEntry


def test_parse_simple_json():
    raw = '[{"itemNumber": 1, "quantity": 14, "referenceDesignator": "C1,C5", "partValue": "100 nF", "mountingType": "SMT"}]'
    entries = _parse_response(raw)
    assert len(entries) == 1
    assert entries[0].item_number == 1
    assert entries[0].quantity == 14
    assert entries[0].reference_designator == "C1,C5"


def test_parse_markdown_fenced():
    raw = '```json\n[{"itemNumber": 2, "quantity": 7, "referenceDesignator": "D2,D9"}]\n```'
    entries = _parse_response(raw)
    assert len(entries) == 1
    assert entries[0].item_number == 2


def test_parse_null_fields():
    raw = '[{"itemNumber": 1, "quantity": 1, "referenceDesignator": "R1", "partValue": null, "manufacturer": null}]'
    entries = _parse_response(raw)
    assert entries[0].part_value is None
    assert entries[0].manufacturer is None
