from __future__ import annotations

import json

import httpx

from ariadne.config import DeepSeekConfig
from ariadne.models import BOMEntry

SYSTEM_PROMPT = """You are a BOM (Bill of Materials) extraction assistant.
Extract component data from the provided text and return ONLY a JSON array.
Each object must have these fields:
- itemNumber: int (row number)
- quantity: int
- referenceDesignator: string (e.g. "C1,C5,C7")
- partValue: string or null
- manufacturer: string or null
- manufacturerOrderCode: string or null
- package: string or null
- mountingType: "SMT" or "THT" (detect from package type)
- notes: string or null

Rules:
- If mounting type cannot be determined, default to "SMT"
- Return ONLY the JSON array, no explanation, no markdown
- If a field is unknown, use null"""


class DeepSeekClient:
    def __init__(self, config: DeepSeekConfig):
        self._config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    def extract_bom(self, text: str, system_prompt: str | None = None) -> list[BOMEntry]:
        prompt = system_prompt or SYSTEM_PROMPT

        response = self._client.post("/v1/chat/completions", json={
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "max_tokens": self._config.max_tokens,
            "temperature": 0.0,
        })
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        return _parse_response(content)

    def close(self):
        self._client.close()


def _parse_response(raw: str) -> list[BOMEntry]:
    json_str = raw.strip()
    if json_str.startswith("```"):
        first_newline = json_str.index("\n")
        last_fence = json_str.rfind("```")
        if first_newline > 0 and last_fence > first_newline:
            json_str = json_str[first_newline + 1:last_fence].strip()

    data = json.loads(json_str)
    return [BOMEntry(
        item_number=item.get("itemNumber", 0),
        quantity=item.get("quantity", 1),
        reference_designator=item.get("referenceDesignator", ""),
        part_value=item.get("partValue"),
        package=item.get("package"),
        manufacturer=item.get("manufacturer"),
        manufacturer_order_code=item.get("manufacturerOrderCode"),
        mounting_type=item.get("mountingType", "SMT"),
        notes=item.get("notes"),
    ) for item in data]
