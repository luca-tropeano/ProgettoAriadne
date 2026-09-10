"""Genera MDF JSON per-famiglia (KEMET/YAGEO MLCC) dai dati della
Material Composition Declaration YAGEO ``test_data/mdf/MCD-Ceramic.pdf``.

Legge il censimento (``mdf_prospecting/census_all.json``), seleziona i
componenti coperti dalla family MCD in ``ariadne.mdf_rules`` (KEMET MLCC
``C<case>C<val>...``, YAGEO CC ``CC<case>...``) ed emette un MDF
JSON per (db, device) con i materiali dichiarati e il link verso le
BOMEntry reali via reference_designator.

Formato: vedere ``ingest_from_json`` in ``ariadne/mdf_ingestor.py``.

Uso::

    python scripts/generate_family_mdf_json.py

Output: ``test_data/mdf/MDF_MCD_MLCC_<db>_<device>.json``
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ariadne.mdf_pdf_parser import parse_pdf_mdf  # noqa: E402
from ariadne.mdf_rules import family_mcd_file  # noqa: E402

CENSUS = ROOT / "mdf_prospecting" / "census_all.json"
MCD_PDF = ROOT / "test_data" / "mdf" / "MCD-Ceramic.pdf"
OUT_DIR = ROOT / "test_data" / "mdf"


def _slug(device: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", device).strip("_")


def main() -> None:
    if not MCD_PDF.exists():
        print(f"[skip] MCD mancante: {MCD_PDF}")
        return

    pdf = parse_pdf_mdf(str(MCD_PDF))
    substances = [(s.name.strip(), s.cas, s.mass_mg) for s in pdf.substances]
    if not substances:
        print("[err] nessuna sostanza parsata da MCD-Ceramic.pdf")
        return
    print(f"[ok] sostanze da MCD-Ceramic.pdf: {len(substances)}")

    rows = json.loads(CENSUS.read_text(encoding="utf-8"))
    per_device: dict[tuple, list[dict]] = {}
    for r in rows:
        mpn = (r.get("mpn") or "").strip()
        if not family_mcd_file(r.get("manufacturer") or "", mpn):
            continue
        per_device.setdefault((r["db"], r["device"]), []).append(r)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (db, device), comps in sorted(per_device.items()):
        material_names = []
        for name, cas, _mass in substances:
            if name not in material_names:
                material_names.append(name)
        materials = [
            {"material_name": name, "casrn": cas, "category": "element"}
            for name, (_, cas, _mass) in zip(material_names, substances)
            if name
        ]
        links = []
        for c in comps:
            refs = [r for r in re.split(r"[,\s]+", c["designators"]) if r]
            for ref in refs:
                for name, _cas, mass in substances:
                    links.append(
                        {
                            "reference_designator": ref,
                            "material_name": name,
                            "mass_mg": mass,
                            "note": (
                                "MCD per-serie YAGEO MLCC/X7R-C0G "
                                "(Material Composition Declaration)"
                            ),
                            "source_mdf": "MCD-Ceramic.pdf",
                        }
                    )
        payload = {
            "device_model": device,
            "materials": materials,
            "links": links,
            "meta": {
                "generated_from": "test_data/mdf/MCD-Ceramic.pdf",
                "source": (
                    "https://yageogroup.com/content/Resource%20Library/"
                    "Material%20Declaration/MCD-Ceramic.pdf"
                ),
                "coverage": "KEMET/YAGEO MLCC SMD (X7R/X5R/C0G)",
                "note": (
                    "dichiarazione di famiglia: la massa si riferisce a un "
                    "componente rappresentativo, non al singolo part"
                ),
            },
        }
        dest = OUT_DIR / f"MDF_MCD_MLCC_{db}_{_slug(device)}.json"
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        n_refs = len({l["reference_designator"] for l in links})
        print(f"[ok] {dest.name}: {len(comps)} gruppi / {n_refs} reference / {len(links)} link")


if __name__ == "__main__":
    main()