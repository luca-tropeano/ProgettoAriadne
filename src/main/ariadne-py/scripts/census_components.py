from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

DB_DEFAULTS = [
    (Path(__file__).resolve().parent.parent / "demo.db", "demo"),
    (Path(__file__).resolve().parent.parent / "ariadne.db", "ariadne"),
]


def _clean(value: str | None) -> str:
    if value is None:
        return ""
    v = value.strip()
    for marker in ("2.2k", "10k"):
        pass
    return v


def census(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT d.id AS device_id, d.brand, d.model_name,
               b.reference_designator, b.part_value, b.manufacturer,
               b.manufacturer_order_code, b.package, b.quantity
        FROM device d
        JOIN bom_entry b ON b.device_id = d.id
        ORDER BY d.model_name, b.manufacturer, b.manufacturer_order_code
        """
    ).fetchall()

    groups: dict[tuple, dict] = {}
    for r in rows:
        key = (
            r["model_name"],
            _clean(r["manufacturer"]),
            _clean(r["manufacturer_order_code"]),
            _clean(r["part_value"]),
            _clean(r["package"]),
        )
        g = groups.setdefault(
            key,
            {
                "device": r["model_name"],
                "brand": r["brand"] or "",
                "designators": [],
                "part_value": _clean(r["part_value"]),
                "manufacturer": _clean(r["manufacturer"]),
                "mpn": _clean(r["manufacturer_order_code"]),
                "package": _clean(r["package"]),
                "quantity": 0,
            },
        )
        g["designators"].append(r["reference_designator"])
        g["quantity"] += int(r["quantity"] or 0)

    conn.close()
    result = []
    for g in groups.values():
        g["designators"] = ", ".join(sorted(g["designators"]))
        result.append(g)
    return result


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "mdf_prospecting"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    for db_path, label in DB_DEFAULTS:
        if not db_path.exists():
            print(f"[skip] {db_path.name} non trovato")
            continue
        rows = census(db_path)
        for row in rows:
            row["db"] = label
        all_rows.extend(rows)
        (out_dir / f"census_{label}.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[ok] {db_path.name}: {len(rows)} gruppi componenti")

    mps = {(r["manufacturer"], r["mpn"]) for r in all_rows if r["mpn"]}
    finals = [k for k in mps if not _is_generic(k[1])]
    print(f"[ok] totale gruppi: {len(all_rows)} | MPN distinti: {len(mps)} | non generici: {len(finals)}")

    (out_dir / "census_all.json").write_text(
        json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _is_generic(mpn: str) -> bool:
    upper = mpn.upper()
    if not mpn:
        return True
    return upper in {
        "NO COMPONENTS",
        "NOT_POPULATED_0603",
        "NOT_POPULATED",
        "DNF",
        "NP",
        "N.A.",
        "NONE",
    }


if __name__ == "__main__":
    main()