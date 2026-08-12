import pytest

from ariadne.ai_client import _parse_response, _parse_usage
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


def test_parse_usage_counts():
    usage = _parse_usage({"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 50
    assert usage.total_tokens == 150


def test_parse_usage_empty():
    usage = _parse_usage(None)
    assert usage.total_tokens == 0
    assert usage.cost_usd == 0.0


def test_parse_usage_cost_positive():
    usage = _parse_usage({"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000})
    assert usage.cost_usd == pytest.approx(0.42)
    assert usage.total_tokens == 2_000_000
