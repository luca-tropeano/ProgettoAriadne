"""Parser for KiCad Interactive HTML BOM (IBOM) files.

IBOM exports a single self-contained ``.html`` file whose BOM table is
serialised inside a base64 LZ-String-compressed JSON payload stored in the
``pcbdata`` JavaScript variable::

    var pcbdata = JSON.parse(LZString.decompressFromBase64("..."))

The decompressed object exposes (among board geometry)::

    pcbdata.metadata        -> {title, revision, company, date}
    pcbdata.bom.fields      -> { "<value index>": [value, footprint], ... }
    pcbdata.bom.both        -> [[[ref, value_index], ...], ...]  (one group per row)
    pcbdata.bom.F / bom.B   -> same structure for front/back layers
    pcbdata.bom.skipped     -> list of value indices marked Do-Not-Populate

Each ``both``/``F``/``B`` row is a single BOM group: every reference in the
row shares the same value/footprint, so the group maps onto one BOMEntry
(with ``quantity`` = number of references and designators comma-joined).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ariadne.csv_parser import _detect_mounting_type
from ariadne.lzstring import decompress_from_base64
from ariadne.models import BOMEntry

_PCBDATA_RE = re.compile(
    r'var\s+pcbdata\s*=\s*JSON\.parse\(LZString\.decompressFromBase64\("([^"]+)"\)\)'
)


def parse_ibom_bom(file_path: str) -> list[BOMEntry]:
    """Parse a KiCad Interactive HTML BOM file into ``BOMEntry`` list."""
    path = Path(file_path)
    html = path.read_text(encoding="utf-8", errors="replace")

    match = _PCBDATA_RE.search(html)
    if not match:
        raise ValueError(
            "Not a KiCad Interactive HTML BOM: pcbdata payload not found"
        )

    payload = decompress_from_base64(match.group(1))
    if not payload:
        raise ValueError("Could not decompress IBOM pcbdata payload")

    data = json.loads(payload)
    bom = data.get("bom")
    if not isinstance(bom, dict) or not isinstance(bom.get("fields"), dict):
        raise ValueError("IBOM payload missing bom.fields table")

    fields = bom["fields"]
    skipped = set(bom.get("skipped") or [])

    # `both` is the merged BOM table; when populated it already covers the
    # front/back layers (F/B may duplicate it), so it takes precedence.
    both = bom.get("both")
    if isinstance(both, list) and both:
        layers = [both]
    else:
        layers = [bom.get("F"), bom.get("B")]
    layers = [rows for rows in layers if isinstance(rows, list)]

    entries: list[BOMEntry] = []
    item_number = 0

    for rows in layers:
        for row in rows:
            pairs = [(r, i) for r, i in row if i not in skipped]
            if not pairs:
                continue
            refs = [r for r, _ in pairs]
            value_index = pairs[0][1]
            value, footprint = _resolve(fields, value_index)

            item_number += 1
            entries.append(
                BOMEntry(
                    item_number=item_number,
                    quantity=len(refs),
                    reference_designator=",".join(refs),
                    part_value=_clean(value),
                    package=_clean(footprint),
                    mounting_type=_detect_mounting_type(footprint, value),
                )
            )

    return entries


def _resolve(fields: dict, value_index: int) -> tuple[str | None, str | None]:
    raw = fields.get(str(value_index))
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return None, None
    return _clean(raw[0]), _clean(raw[1])


def _clean(text) -> str | None:
    if text is None:
        return None
    value = str(text).strip()
    if value.lower() in ("", "~", "empty"):
        return None
    return value
