import pytest

from ariadne.ai_client import DeepSeekClient, SYSTEM_PROMPT, _parse_response, _parse_usage
from ariadne.config import DeepSeekConfig
from ariadne.models import BOMEntry


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _ok_response():
    return FakeResponse({
        "choices": [{
            "message": {
                "content": '[{"itemNumber": 3, "quantity": 2, "referenceDesignator": "Q1,Q2", "partValue": "2N2222", "mountingType": "THT"}]'
            }
        }],
        "usage": {"prompt_tokens": 120, "completion_tokens": 40, "total_tokens": 160},
    })


def test_extract_bom_makes_request_and_parses(monkeypatch):
    captured = {}

    def fake_post(self, url, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return _ok_response()

    monkeypatch.setattr("ariadne.ai_client.httpx.Client.post", fake_post)
    client = DeepSeekClient(DeepSeekConfig(api_key="test-key", model="test-model"))
    try:
        result = client.extract_bom("some bom text")
        assert captured["url"] == "/v1/chat/completions"
        assert captured["json"]["model"] == "test-model"
        assert captured["json"]["max_tokens"] == 2000
        assert captured["json"]["temperature"] == 0.0
        messages = captured["json"]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT
        assert messages[1] == {"role": "user", "content": "some bom text"}
        assert len(result.entries) == 1
        assert result.entries[0].reference_designator == "Q1,Q2"
        assert result.entries[0].mounting_type == "THT"
        assert result.usage.total_tokens == 160
        assert result.usage.prompt_tokens == 120
    finally:
        client.close()


def test_extract_bom_custom_system_prompt(monkeypatch):
    captured = {}

    def fake_post(self, url, **kwargs):
        captured["json"] = kwargs["json"]
        return _ok_response()

    monkeypatch.setattr("ariadne.ai_client.httpx.Client.post", fake_post)
    client = DeepSeekClient(DeepSeekConfig(api_key="k"))
    try:
        client.extract_bom("text", system_prompt="CUSTOM PROMPT")
        assert captured["json"]["messages"][0]["content"] == "CUSTOM PROMPT"
    finally:
        client.close()


def test_extract_bom_http_error_raises(monkeypatch):
    def fake_post(self, url, **kwargs):
        return FakeResponse({"error": "boom"}, status_code=500)

    monkeypatch.setattr("ariadne.ai_client.httpx.Client.post", fake_post)
    client = DeepSeekClient(DeepSeekConfig(api_key="k"))
    try:
        with pytest.raises(RuntimeError):
            client.extract_bom("text")
    finally:
        client.close()


def test_extract_bom_custom_max_tokens(monkeypatch):
    captured = {}

    def fake_post(self, url, **kwargs):
        captured["json"] = kwargs["json"]
        return _ok_response()

    monkeypatch.setattr("ariadne.ai_client.httpx.Client.post", fake_post)
    client = DeepSeekClient(DeepSeekConfig(api_key="k", max_tokens=500))
    try:
        client.extract_bom("text")
        assert captured["json"]["max_tokens"] == 500
    finally:
        client.close()


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


def test_parse_usage_total_falls_back_to_sum():
    usage = _parse_usage({"prompt_tokens": 10, "completion_tokens": 5})
    assert usage.total_tokens == 15


def test_parse_usage_partial_keys_default_zero():
    usage = _parse_usage({})
    assert usage.total_tokens == 0
    assert usage.cost_usd == 0.0
