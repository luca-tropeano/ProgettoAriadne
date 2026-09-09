"""Ingestione MDF (Material Data File).

Obiettivo del pipeline: estrarre i materiali dai datasheet dei componenti
(MDF, tipicamente PDF) e collegarli alle BOMEntry. Questo modulo espone tre
percorsi di parsing:

- ``ingest_from_json(path)`` — PERCORSO ad-hoc: legge un file JSON con il
  formato documentato qui sotto e popola ``material`` e ``component_material``.

- ``ingest_from_xml(path)`` — PERCORSO IPC-1752: legge una "Material
  Composition Declaration" Class D (XML IPC-1752A/B, schema ufficiale
  ``http://webstds.ipc.org/175x/2.0``) e popola ``material`` +
  ``component_material``. Il matching verso la BOM avviene per part number
  (es. il murata ``GRM188R61E225MA12D`` ritrovato nel
  ``part_value``/``manufacturer_order_code`` delle BOMEntry).

- ``ingest_from_pdf(path)`` — PERCORSO PDF: parsa le tabelle delle Material
  Declaration (pdfplumber) nei layout ZVEI per-componente e KEMET/YAGEO
  per-serie (vedi ``ariadne.mdf_pdf_parser``). I materiali vengono sempre
  inseriti; il collegamento alla BOM avviene solo se nel PDF compare un part
  number (pattern Murata GRM / KEMET C·, L·) trovato nella BOM — altrimenti
  warning "materials inseriti ma non collegati".

Formato JSON accettato::

    {
      "device_model": "Inkplate 5",                 // opzionale, per risolvere i link
      "materials": [
        {"material_name": "Copper", "casrn": "7440-50-8", "category": "element"}
      ],
      "links": [
        {"reference_designator": "C1", "material_name": "Copper",
         "mass_mg": 12.5, "note": "stub", "source_mdf": "MDF_KEMET_C0603.pdf"}
      ]
    }

I reference_designator possono riferirsi a singole reference o a gruppi
già uniti con virgola nell'import BOM (es. "C1" dentro "C1,C2,C3").
"""

from __future__ import annotations

import json
from pathlib import Path

from ariadne.database import Database
from ariadne.ipc1752 import DeclaredSubstance, HomogeneousMaterial
from ariadne.mdf_pdf_parser import parse_pdf_mdf
from ariadne.models import Material


def _substance_mass_mg(sub: DeclaredSubstance, hm_mass_mg: float | None) -> float:
    """Massa in mg della sostanza nel componente.

    Priorità: massa assoluta dichiarata → concentrazione percentuale × massa
    del materiale omogeneo → 0 (non dichiarata).
    """
    if sub.mass_mg is not None:
        return round(sub.mass_mg, 6)
    if sub.concentration_pct is not None and hm_mass_mg is not None:
        return round(hm_mass_mg * sub.concentration_pct / 100.0, 6)
    return 0.0


def _dedupe_by_id(rows: list[dict]) -> list[dict]:
    """Rimuove duplicati da una lista di righe di BOMEntry (stesso id)."""
    seen: set[int] = set()
    unique: list[dict] = []
    for row in rows:
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        unique.append(row)
    return unique

JSON_FORMAT_DOC = {
    "device_model": "Inkplate 5",
    "materials": [
        {"material_name": "Copper", "casrn": "7440-50-8", "category": "element"}
    ],
    "links": [
        {"reference_designator": "C1", "material_name": "Copper",
         "mass_mg": 12.5, "note": "stub", "source_mdf": "MDF_KEMET_C0603.pdf"}
    ],
}


class MDFIngestResult:
    """Risultato di un'ingestione MDF."""

    def __init__(self) -> None:
        self.materials_created = 0
        self.materials_skipped = 0
        self.links_created = 0
        self.links_skipped = 0
        self.warnings: list[str] = []

    def to_dict(self) -> dict:
        return {
            "materials_created": self.materials_created,
            "materials_skipped": self.materials_skipped,
            "links_created": self.links_created,
            "links_skipped": self.links_skipped,
            "warnings": self.warnings,
        }


class MDFIngestor:
    """Stub di ingestione MDF verso il DB SQLite locale."""

    def __init__(self, db: Database):
        self._db = db

    def ingest(self, file_path: str) -> MDFIngestResult:
        """Dispatcher per estensione: JSON → ad-hoc, XML → IPC-1752 Class D, PDF → tabelle."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".json":
            return self.ingest_from_json(str(path))
        if suffix == ".xml":
            return self.ingest_from_xml(str(path))
        if suffix == ".pdf":
            return self.ingest_from_pdf(str(path))
        raise NotImplementedError(
            f"Ingestione MDF da '{path.suffix or path.name}' non implementata. "
            "JSON (ad-hoc), XML (IPC-1752A/B Class D) e PDF (Material Declaration, "
            "pdfplumber) supportati."
        )

    def ingest_from_json(self, file_path: str) -> MDFIngestResult:
        """Popola material + component_material da un file JSON (formato sopra)."""
        path = Path(file_path)
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        result = MDFIngestResult()

        device_id = None
        if data.get("device_model"):
            device = self._db.get_device(data["device_model"])
            if device:
                device_id = device["id"]
            else:
                result.warnings.append(
                    f"Device '{data['device_model']}' non trovato; link non collegati"
                )

        material_ids: dict[str, int] = {}
        for m in data.get("materials", []):
            material = Material(
                material_name=str(m.get("material_name", "")).strip(),
                casrn=m.get("casrn"),
                category=m.get("category") or "element",
            )
            if not material.material_name:
                result.warnings.append("Saltato materiale senza material_name")
                continue
            mid = self._db.insert_material(material)
            if mid is None:
                mid = self._db.get_material_id(material.material_name)
                result.materials_skipped += 1
            else:
                result.materials_created += 1
            material_ids[material.material_name] = mid

        for link in data.get("links", []):
            material_name = str(link.get("material_name", "")).strip()
            ref = str(link.get("reference_designator", "")).strip()
            mid = material_ids.get(material_name) or self._db.get_material_id(material_name)
            if mid is None:
                result.warnings.append(
                    f"Link saltato: materiale '{material_name}' non presente in 'materials'"
                )
                result.links_skipped += 1
                continue
            if device_id is None:
                result.links_skipped += 1
                continue
            entry = self._db.find_bom_entry_by_ref(device_id, ref)
            if entry is None:
                result.warnings.append(
                    f"Link saltato: '{ref}' non trovato nel device '{data['device_model']}'"
                )
                result.links_skipped += 1
                continue
            linked = self._db.link_material(
                entry["id"],
                mid,
                mass_mg=float(link.get("mass_mg") or 0.0),
                note=link.get("note"),
                source_mdf=link.get("source_mdf"),
            )
            if linked is None:
                result.links_skipped += 1
            else:
                result.links_created += 1

        return result

    def ingest_from_xml(self, file_path: str) -> MDFIngestResult:
        """Popola material + component_material da un IPC-1752A/B Class D (XML).

        Le sostanze dichiarate diventano ``material`` (nome + CAS). Ogni
        sostanza viene collegata alle BOMEntry il cui part number matcherà
        l'itemNumber dichiarato nel file. La massa del link è presa dalla massa
        assoluta dichiarata, oppure calcolata come
        ``massa_materiale_omogeneo × concentrazione%``.
        """
        path = Path(file_path)
        from ariadne.ipc1752 import parse_class_d_xml

        xml_text = path.read_text(encoding="utf-8", errors="replace")
        products = parse_class_d_xml(xml_text)
        result = MDFIngestResult()

        material_ids: dict[str, int] = {}
        for product in products:
            if not product.item_numbers:
                result.warnings.append(
                    "Prodotto IPC-1752 senza itemNumber: materials inseriti ma non collegati"
                )

            entries = _dedupe_by_id(
                [
                    row
                    for item_no in product.item_numbers
                    for row in self._db.find_bom_entry_by_part_number(item_no)
                ]
            )
            if not entries and product.item_numbers:
                result.warnings.append(
                    f"Part number '{', '.join(product.item_numbers)}' non trovato in BOM; "
                    "materials inseriti ma non collegati"
                )

            for hm in product.homogeneous_materials:
                for sub in hm.substances:
                    material = Material(
                        material_name=sub.name.strip(),
                        casrn=sub.cas,
                        category="element",
                    )
                    mid = material_ids.get(material.material_name)
                    if mid is None:
                        mid = self._db.insert_material(material)
                        if mid is None:
                            mid = self._db.get_material_id(material.material_name)
                            result.materials_skipped += 1
                        else:
                            result.materials_created += 1
                        material_ids[material.material_name] = mid

                    mass_mg = _substance_mass_mg(sub, hm.mass_mg)
                    for entry in entries:
                        linked = self._db.link_material(
                            entry["id"],
                            mid,
                            mass_mg=mass_mg,
                            note=(
                                f"IPC-1752 Class D: {hm.name}"
                                f"({hm.material_group or 'material group non dichiarato'})"
                            ),
                            source_mdf=path.name,
                        )
                        if linked is None:
                            result.links_skipped += 1
                        else:
                            result.links_created += 1

        return result

    def ingest_from_pdf(self, file_path: str) -> MDFIngestResult:
        """Popola material + component_material da un PDF Material Declaration.

        Parsa le tabelle con ``mdf_pdf_parser.parse_pdf_mdf`` (layout ZVEI
        per-componente e KEMET/YAGEO per-serie). Ogni sostanza dichiarata
        diventa un ``material`` (nome + CAS); i CAS placeholder (system, pseudo
        substance, -) vengono scartati. Il collegamento verso BOM avviene solo
        per i part number trovati nel testo del PDF e risolti nella BOM.
        """
        pdf = parse_pdf_mdf(file_path)
        result = MDFIngestResult()
        result.warnings.extend(pdf.warnings)
        path = Path(file_path)

        entries: list[dict] = []
        if pdf.part_numbers:
            entries = _dedupe_by_id(
                [
                    row
                    for pn in pdf.part_numbers
                    for row in self._db.find_bom_entry_by_part_number(pn)
                ]
            )
            if not entries:
                result.warnings.append(
                    f"Part number '{', '.join(pdf.part_numbers)}' trovato nel PDF ma non in BOM; "
                    "materials inseriti ma non collegati"
                )
        else:
            result.warnings.append(
                "Nessun part number riconosciuto nel PDF; materials inseriti ma non collegati"
            )

        material_ids: dict[str, int] = {}
        for sub in pdf.substances:
            material = Material(
                material_name=sub.name.strip(),
                casrn=sub.cas,
                category="element",
            )
            mid = material_ids.get(material.material_name)
            if mid is None:
                mid = self._db.insert_material(material)
                if mid is None:
                    mid = self._db.get_material_id(material.material_name)
                    result.materials_skipped += 1
                else:
                    result.materials_created += 1
                material_ids[material.material_name] = mid

            mass_mg = _substance_mass_mg(sub, pdf.total_mass_mg)
            note = f"MDF PDF (pdfplumber): '{pdf.component_name or '-'}'"
            for entry in entries:
                linked = self._db.link_material(
                    entry["id"],
                    mid,
                    mass_mg=mass_mg,
                    note=note,
                    source_mdf=path.name,
                )
                if linked is None:
                    result.links_skipped += 1
                else:
                    result.links_created += 1

        return result

    def close(self):
        self._db.close()