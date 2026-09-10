from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from ariadne.models import BOMEntry


def _detect_mounting_type(package: str | None, value: str | None = None) -> str:
    pkg = (package or "").upper()
    val = (value or "").upper()

    for prefix in ("SMD_", "CHIP_", "QFP", "LQFP", "TQFP", "BGA", "SSOP",
                    "TSSOP", "MSOP", "DFN", "QFN", "WLCSP", "TSOP"):
        if prefix in pkg:
            return "SMT"

    for prefix in ("DIP", "SIP", "TO-", "TO92", "DO-35", "DO-41",
                    "RAxial", "CP_Radial", "C_Rect"):
        if prefix in pkg:
            return "THT"

    if "THT" in pkg or "TH_" in pkg or "PTH" in pkg or "VERTICAL" in pkg or "HORIZONTAL" in pkg:
        return "THT"
    if "SMD" in pkg or "SM_" in pkg or "SMT" in pkg:
        return "SMT"

    if "SOT" in pkg:
        return "SMT"
    if "DSUB" in pkg or "CONNECTOR" in pkg or "ISA" in pkg or "ZORRO" in pkg:
        return "THT"
    if "0603" in pkg or "0805" in pkg or "1206" in pkg or "1005" in pkg:
        return "SMT"

    if "1N4148" in val or "1N400" in val:
        return "THT"

    return "SMT"


def _split_designators(text: str) -> str:
    text = text.strip().strip('"').strip()
    text = text.replace(";", ",")
    if "," in text:
        parts = [p.strip() for p in text.split(",") if p.strip()]
    else:
        parts = [p.strip() for p in text.split() if p.strip()]
    expanded = []
    for p in parts:
        expanded.extend(_expand_range(p))
    return ",".join(expanded) if expanded else text


_RANGE_RE = re.compile(
    r"^([A-Za-z]+)(\d+)\s*[-\u2013\u2014\u2010]\s*([A-Za-z]+)(\d+)([A-Za-z]*)$"
)


def _expand_range(token: str) -> list[str]:
    """Espande un reference range tipo ``C1-C10`` in ``C1,...,C10``.

    Richiede lo stesso prefisso alfanumerico sui due estremi (``C1-C10``),
    senza padding: ``C1-C10`` -> C1..C10. Costruzioni tipo ``USB-2`` o
    ``TP-5V`` non matchano (serve una cifra subito dopo il prefisso iniziale).
    """
    m = _RANGE_RE.match(token)
    if not m:
        return [token]
    prefix, start_s, prefix2, end_s, suffix = m.groups()
    if prefix.upper() != prefix2.upper():
        return [token]
    try:
        start, end = int(start_s), int(end_s)
    except ValueError:
        return [token]
    if start <= 0 or end < start:
        return [token]
    return [f"{prefix}{i}{suffix}" for i in range(start, end + 1)]


_KNOWN = {
    "ref": "ref", "reference": "ref", "designator": "ref",
    "qty": "qty", "quantity": "qty",
    "value": "value", "designation": "value", "part/value": "value", "part": "value",
    "footprint": "package", "package": "package", "foot print": "package",
    "mouserpn": "mouser", "mouser_pn": "mouser", "supplier order code": "mouser",
    "supplier": "supplier", "supplier and ref": "supplier",
    "donotpopulate": "dnp", "do not populate": "dnp", "dnp": "dnp",
    "gender": "gender",
    "datasheet": "datasheet",
}


def _map_columns(headers: list[str], known: dict = _KNOWN) -> dict:
    """Mappa gli header di una tabella (CSV o Markdown) su chiavi semantiche.

    Prima match esatto, poi substring (first-wins), come nel parser CSV.
    Ritorna ``{"ref": 0, "qty": 1, ...}`` con gli indici delle colonne.
    """
    col: dict = {}
    for i, h in enumerate(headers):
        clean = h.strip().strip('"').lower()
        mapped = known.get(clean)
        if mapped is None:
            for key, value in known.items():
                if key in clean:
                    mapped = value
                    break
        if mapped and mapped not in col:
            col[mapped] = i
    return col


def _cell(col: dict, key: str, row_vals: list[str]) -> str | None:
    """Valore pulito di ``key`` dalla riga, o None se assente/vuoto."""
    idx = col.get(key)
    if idx is None or idx >= len(row_vals):
        return None
    value = row_vals[idx].strip().strip('"')
    if value.lower() in ("", "~"):
        return None
    return value


def parse_csv_bom(file_path: str) -> list[BOMEntry]:
    path = Path(file_path)
    raw = path.read_text(encoding="utf-8", errors="replace")

    delim = "," if ";" not in raw.split("\n")[0] else ";"
    reader = csv.DictReader(io.StringIO(raw), delimiter=delim)
    if reader.fieldnames is None:
        return []

    headers = [h.strip().strip('"').lower() for h in reader.fieldnames]

    col = _map_columns(headers)

    ref_key = next((k for k in ("ref", "reference", "designator") if k in col), None)
    qty_key = next((k for k in ("qty", "quantity") if k in col), None)
    if ref_key is None or qty_key is None:
        return []

    entries = []
    item_number = 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for row_raw in f:
            row_raw = row_raw.strip()
            if not row_raw or row_raw.startswith("#") or row_raw.startswith("//"):
                continue

            row_vals = next(csv.reader([row_raw], delimiter=delim))
            row_vals = [v.strip().strip('"') for v in row_vals]

            if not col.get("ref") and not col.get("qty"):
                continue
            if col.get("ref") is not None and col["ref"] < len(row_vals):
                if row_vals[col["ref"]].lower() in ("ref", "designator", "reference"):
                    continue

            try:
                ref_text = row_vals[col[ref_key]].strip().strip('"')
                qty_text = row_vals[col[qty_key]].strip().strip('"')
            except (IndexError, KeyError):
                continue

            if not ref_text or not qty_text:
                continue

            try:
                quantity = int(qty_text)
            except ValueError:
                continue

            designators = _split_designators(ref_text)
            if not designators:
                continue

            value_text = None
            if "value" in col and col["value"] < len(row_vals):
                v = row_vals[col["value"]].strip().strip('"')
                if v.lower() not in ("", "empty", "~"):
                    value_text = v

            package_text = None
            if "package" in col and col["package"] < len(row_vals):
                p = row_vals[col["package"]].strip().strip('"')
                if p.lower() not in ("", "~"):
                    package_text = p

            mouser_text = None
            if "mouser" in col and col["mouser"] < len(row_vals):
                m = row_vals[col["mouser"]].strip().strip('"')
                if m.lower() not in ("", "~"):
                    mouser_text = m

            supplier_text = None
            if "supplier" in col and col["supplier"] < len(row_vals):
                s = row_vals[col["supplier"]].strip().strip('"')
                if s.lower() not in ("", "~"):
                    supplier_text = s

            dnp = False
            if "dnp" in col and col["dnp"] < len(row_vals):
                dnp = row_vals[col["dnp"]].strip().strip('"').lower() == "yes"

            gender_text = None
            if "gender" in col and col["gender"] < len(row_vals):
                g = row_vals[col["gender"]].strip().strip('"')
                if g.lower() not in ("", "~"):
                    gender_text = g

            item_number += 1
            entries.append(BOMEntry(
                item_number=item_number,
                quantity=quantity,
                reference_designator=designators,
                part_value=value_text,
                package=package_text,
                mounting_type=_detect_mounting_type(package_text, value_text),
                supplier_order_code=mouser_text,
                supplier=supplier_text or gender_text,
                notes="DNP" if dnp else None,
            ))

    return entries
