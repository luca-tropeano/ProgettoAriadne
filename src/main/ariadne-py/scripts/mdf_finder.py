"""Report per-componente delle fonti MDF (usa ``ariadne.mdf_rules``).

Per ogni gruppo componente nel censimento (``mdf_prospecting/census_all.json``)
ripete la stessa classificazione del sourcing automatico (family_mcd /
reference / no_mpn) e scrive ``mdf_prospecting/mdf_report.csv`` e
``.json``. È la versione "statica" del pipeline automatico
(``ariadne.mdf_auto``), utile per audit e documentazione.

Uso::

    python scripts/mdf_finder.py
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ariadne.mdf_rules import classify  # noqa: E402

CENSUS = ROOT / "mdf_prospecting" / "census_all.json"
OUT_DIR = ROOT / "mdf_prospecting"

BASE_FIELDS = [
    "db", "device", "designators", "part_value", "manufacturer", "mpn",
    "package", "quantity",
]


def classify_row(row: dict) -> dict:
    info = classify(row.get("manufacturer") or "", row.get("mpn") or "")
    report = {
        "status": info["status"],
        "mdf_file": (
            f"test_data/mdf/{info['mdf_file']}" if info.get("mdf_file") else ""
        ),
        "reference_url": info.get("reference_url", ""),
        "note": info.get("note", ""),
    }
    base = {k: row.get(k, "") for k in BASE_FIELDS}
    base["manufacturer"] = info["manufacturer"]
    return {**base, **report}


def main() -> None:
    if not CENSUS.exists():
        print(f"[skip] censimento mancante: {CENSUS}")
        return
    rows = json.loads(CENSUS.read_text(encoding="utf-8"))
    report = [classify_row(r) for r in rows]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "mdf_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with (OUT_DIR / "mdf_report.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=BASE_FIELDS + [
            "status", "mdf_file", "reference_url", "note",
        ])
        writer.writeheader()
        writer.writerows(report)

    counts = Counter(r["status"] for r in report)
    family_files = sorted({r["mdf_file"] for r in report if r["mdf_file"]})
    print(f"[ok] report: {len(report)} componenti")
    for status, n in counts.most_common():
        print(f"      {status}: {n}")
    print(f"      family MDF usati: {', '.join(family_files) or '-'}")


if __name__ == "__main__":
    main()