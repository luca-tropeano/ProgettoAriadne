"""Confronto tra una BOM già presente e una appena importata.

Espande ogni entry nei suoi reference designator (C1,C2 -> C1 e C2) e confronta
per-ref i campi rilevanti, producendo tre elenchi:
- aggiunti:   ref presenti solo nella nuova BOM
- rimossi:    ref presenti solo nella vecchia BOM
- modificati: ref in comune ma con valore/produttore/codice/qty/package cambiati
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field

import re

_COMPARE_FIELDS = (
    "part_value", "manufacturer", "manufacturer_order_code", "quantity", "package",
)


def _norm(v) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _snap(row: dict) -> dict:
    return {f: _norm(row.get(f)) for f in _COMPARE_FIELDS}


def _expand_row(row: dict) -> dict[str, dict]:
    refs = re.split(r"[\s,;]+", _norm(row.get("reference_designator")))
    snap = _snap(row)
    out: dict[str, dict] = OrderedDict()
    for r in refs:
        if r:
            out[r] = snap
    return out


def _expand_many(rows: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = OrderedDict()
    for row in rows:
        out.update(_expand_row(row))
    return out


@dataclass
class BomDiff:
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    modified: list[dict] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    def as_dict(self) -> dict:
        return {
            "added": self.added,
            "removed": self.removed,
            "modified": self.modified,
        }


def diff_boms(old_entries: list[dict], new_entries: list[dict]) -> BomDiff:
    """Confronta due BOM (lista di dict con reference_designator e i campi di confronto)."""
    old = _expand_many(old_entries)
    new = _expand_many(new_entries)
    diff = BomDiff()
    diff.added = sorted(set(new) - set(old))
    diff.removed = sorted(set(old) - set(new))
    for ref in sorted(set(old) & set(new)):
        if old[ref] != new[ref]:
            diff.modified.append(
                {
                    "ref": ref,
                    "old": old[ref],
                    "new": new[ref],
                }
            )
    return diff