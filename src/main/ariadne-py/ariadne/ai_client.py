from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from ariadne.config import DeepSeekConfig
from ariadne.models import BOMEntry

logger = logging.getLogger("ariadne.ai")

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

# Estimated USD cost per 1M tokens (deepseek-chat). Update if pricing changes.
INPUT_PRICE_PER_1M = 0.14
OUTPUT_PRICE_PER_1M = 0.28


@dataclass
class AIUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class AIExtractionResult:
    entries: list[BOMEntry]
    usage: AIUsage


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

    def extract_bom(self, text: str, system_prompt: str | None = None) -> AIExtractionResult:
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

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        entries = _parse_response(content)
        usage = _parse_usage(data.get("usage"))
        logger.info(
            "DeepSeek usage: prompt=%d completion=%d total=%d est_cost=$%.5f",
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
            usage.cost_usd,
        )
        return AIExtractionResult(entries=entries, usage=usage)

    def close(self):
        self._client.close()


def _parse_usage(raw: dict | None) -> AIUsage:
    if not raw:
        return AIUsage()

    prompt = int(raw.get("prompt_tokens", 0))
    completion = int(raw.get("completion_tokens", 0))
    total = int(raw.get("total_tokens", prompt + completion))
    cost = (prompt / 1_000_000) * INPUT_PRICE_PER_1M + (completion / 1_000_000) * OUTPUT_PRICE_PER_1M
    return AIUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
        cost_usd=round(cost, 6),
    )


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
