"""Parser per BOM in formato Markdown (.md).

Supporta tabelle GitHub-Flavored Markdown del tipo::

    | Ref | Value | Qty | Footprint | Manufacturer | MPN        |
    |-----|-------|-----|-----------|--------------|------------|
    | C1,C2| 100nF | 2   | 0603       | KEMET        | C0603C104  |
    | R1   | 10k   | 1   | 0603       | YAGEO        | RC0603JR-0 |

Colonne riconosciute (match esatto o substring): ``ref`` (obbligatoria),
``qty`` (opzionale, default = numero di reference), ``value``, ``footprint``,
``manufacturer``, ``mpn``/``part number``, ``mouser``, ``supplier``, ``dnp``.
Il testo fuori dalle tabelle viene ignorato; il parser gestisce celle in
``**bold**``/``*italic*`` e ``inline code``.
"""

from __future__ import annotations

import re
from pathlib import Path

from ariadne.csv_parser import _KNOWN, _cell, _detect_mounting_type, _map_columns, _split_designators
from ariadne.models import BOMEntry

# Mappe colonne CSV + colonne Markdown tipiche dei BOM testuali.
_KNOWN_MD: dict = {
    **_KNOWN,
    "reference designator": "ref", "refs": "ref", "designators": "ref",
    "item": "ref", "item number": "ref",
    "count": "qty",
    "mpn": "mpn", "part number": "mpn", "part no": "mpn", "pn": "mpn",
    "manufacturer part number": "mpn", "mfr part no": "mpn", "order code": "mpn",
    "manufacturer": "manufacturer", "mfr": "manufacturer", "brand": "manufacturer",
    "description": "value", "designation": "value",
}

_SEPARATOR_RE = re.compile(r"^[\s|:\-]+$")


def _clean_cell(value: str) -> str:
    """Rimuove markup Markdown (bold/italic/code) da una cella."""
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"\*([^*]+)\*", r"\1", value)
    value = re.sub(r"__([^_]+)__", r"\1", value)
    return value.strip()


def _split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [_clean_cell(c) for c in line.split("|")]


def _is_separator(line: str) -> bool:
    return bool(line) and _SEPARATOR_RE.match(line)


def _extract_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    lines = [ln.rstrip() for ln in text.splitlines()]
    tables = []
    i = 0
    n = len(lines)
    while i < n - 1:
        header, separator = lines[i], lines[i + 1]
        if _is_separator(separator) and header.count("|") >= 1:
            rows = []
            j = i + 2
            while j < n and lines[j].count("|") >= 1:
                if _is_separator(lines[j]):
                    break
                rows.append(_split_row(lines[j]))
                j += 1
            if rows:
                tables.append((_split_row(header), rows))
            i = j
        else:
            i += 1
    return tables


def _is_dnp(value: str | None) -> bool:
    return (value or "").strip().lower() in ("yes", "true", "x", "1", "dnp")


def _parse_int(value: str | None) -> int | None:
    """Intero dalla cella; estrae la prima cifra anche da range tipo ``3-6``."""
    if value is None:
        return None
    match = re.search(r"\d[\d.,]*", value.replace(",", ""))
    if not match:
        return None
    try:
        return int(float(match.group()))
    except ValueError:
        return None


def parse_md_bom(file_path: str) -> list[BOMEntry]:
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    entries = []
    item_number = 0

    for header, rows in _extract_tables(text):
        col = _map_columns(header, _KNOWN_MD)
        ref_key = col.get("ref")
        if ref_key is None:
            continue
        qty_key = col.get("qty")

        for cells in rows:
            if ref_key >= len(cells):
                continue
            ref_text = cells[ref_key].strip()
            if ref_text in ("-", "—", "--", "–") or ref_text.lower() in (
                "ref", "reference", "designator", "item", "component",
            ):
                continue

            designators = _split_designators(ref_text)
            if not designators:
                continue
            ref_count = len(designators.split(","))

            quantity = _parse_int(_cell(col, "qty", cells)) if qty_key is not None else None
            if quantity is None:
                quantity = ref_count

            package = _cell(col, "package", cells)
            value = _cell(col, "value", cells)

            entries.append(BOMEntry(
                item_number=item_number + 1,
                quantity=quantity,
                reference_designator=designators,
                part_value=value,
                package=package,
                manufacturer=_cell(col, "manufacturer", cells),
                manufacturer_order_code=_cell(col, "mpn", cells),
                supplier_order_code=_cell(col, "mouser", cells),
                supplier=_cell(col, "supplier", cells),
                mounting_type=_detect_mounting_type(package, value),
                notes="DNP" if _is_dnp(_cell(col, "dnp", cells)) else None,
            ))
            item_number += 1

    return entries