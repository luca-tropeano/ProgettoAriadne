"""Sourcing MDF automatico all'import di una BOM.

Dopo l'import di un device, ``auto_source_mdf``:

- raggruppa le BOMEntry per (produttore, part number);
- classifica ogni gruppo con ``ariadne.mdf_rules``:
  - ``family_mcd`` → genera e ingerisce un MDF JSON per-famiglia (materiali
    dalla Material Composition Declaration locale, link verso le BOMEntry
    del device); massa e CAS sono quelli dichiarati dal produttore (valori
    rappresentativi di famiglia);
  - ``reference`` → annota la BOMEntry con la pagina ufficiale di
    conformità/MDF del produttore (colonna ``notes`` di ``bom_entry``);
  - ``no_mpn`` → niente da fare (componente generico/DNF).

Il tutto è idempotente: ``link_material`` e ``insert_material`` deduplicano,
quindi ri-importare la stessa BOM non duplica i dati.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import re

from ariadne.database import Database
from ariadne.mdf_ingestor import MDFIngestor
from ariadne.mdf_pdf_parser import parse_pdf_mdf
from ariadne.mdf_rules import MDF_DIR, classify, family_mcd_file

_FAMILY_SUBSTANCES_CACHE: dict[str, tuple] = {}


@dataclass
class AutoMDFResult:
    materials_created: int = 0
    links_created: int = 0
    family_groups: int = 0
    reference_components: int = 0
    no_mpn_components: int = 0
    skipped_missing_mcd: int = 0
    files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def auto_source_mdf(
    db: Database,
    device_model: str,
    mdf_dir: Path | None = None,
) -> AutoMDFResult:
    """Rileva e ingerisce gli MDF per i componenti di un device."""
    mdf_dir = mdf_dir or MDF_DIR
    result = AutoMDFResult()

    device = db.get_device(device_model)
    if device is None:
        result.warnings.append(f"Device '{device_model}' non trovato; MDF auto saltato")
        return result

    entries = db.get_bom_entries(device["id"])
    if not entries:
        return result

    groups: dict[dict] = defaultdict(list)
    for e in entries:
        key = (
            (e.get("manufacturer") or "").strip(),
            (e.get("manufacturer_order_code") or "").strip(),
        )
        groups[key].append(e)

    by_file: dict[str, list[dict]] = defaultdict(list)
    references: list[tuple[int, str]] = []
    for (manuf, mpn), ents in groups.items():
        info = classify(manuf, mpn)
        if info["status"] == "family_mcd":
            by_file[info["mdf_file"]].append(
                {"manufacturer": manuf, "mpn": mpn, "entries": ents}
            )
            result.family_groups += 1
        elif info["status"] == "reference":
            result.reference_components += 1
            for e in ents:
                references.append((e["id"], info.get("reference_url") or ""))
        else:
            result.no_mpn_components += 1

    for entry_id, url in references:
        if url:
            db.annotate_bom_entry(entry_id, f"MDF: {url}")

    ingestor = MDFIngestor(db)
    for file_name, groups_ in by_file.items():
        path = mdf_dir / file_name
        if not path.exists():
            result.warnings.append(f"family MCD mancante: {path.name}")
            result.skipped_missing_mcd += 1
            continue
        payload = _build_family_payload(device_model, path, groups_)
        res = ingestor.ingest_from_dict(payload)
        result.materials_created += res.materials_created
        result.links_created += res.links_created
        result.files.append(path.name)
        result.warnings.extend(res.warnings)

    return result


def _build_family_payload(
    device_model: str,
    mcd_path: Path,
    groups: list[dict],
) -> dict:
    """Costruisce il payload JSON MDF per-famiglia (vedi ingest_from_dict)."""
    substances = _family_substances(mcd_path)

    materials = []
    seen: set[str] = set()
    for sub in substances:
        name = sub.name.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        materials.append(
            {"material_name": name, "casrn": sub.cas, "category": "element"}
        )

    links = []
    for group in groups:
        for entry in group["entries"]:
            ref = _first_reference(entry.get("reference_designator") or "")
            if not ref:
                continue
            for sub in substances:
                name = sub.name.strip()
                if not name:
                    continue
                links.append(
                    {
                        "reference_designator": ref,
                        "material_name": name,
                        "mass_mg": float(sub.mass_mg or 0.0),
                        "note": (
                            "MDF auto — Material Composition Declaration "
                            "per-serie (valori rappresentativi di famiglia)"
                        ),
                        "source_mdf": mcd_path.name,
                    }
                )

    return {"device_model": device_model, "materials": materials, "links": links}


def _family_substances(mcd_path: Path) -> tuple:
    key = str(mcd_path)
    if key not in _FAMILY_SUBSTANCES_CACHE:
        _FAMILY_SUBSTANCES_CACHE[key] = parse_pdf_mdf(key).substances
    return _FAMILY_SUBSTANCES_CACHE[key]


def _first_reference(designators: str) -> str:
    for token in re.split(r"[\s,]+", designators):
        if token:
            return token
    return ""