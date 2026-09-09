from __future__ import annotations

import sqlite3
from pathlib import Path

from ariadne.config import DatabaseConfig
from ariadne.models import BOMEntry, Device, ImportResult, Material


def _normalize_part(value: str | None) -> str:
    """MPN normalizzato per confronti (maiuscolo, senza spazi/trattini)."""
    if not value:
        return ""
    return "".join(ch for ch in value.upper() if not ch.isspace() and ch != "-")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS device (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL DEFAULT '',
    model_name TEXT NOT NULL UNIQUE,
    manufacturer TEXT NOT NULL DEFAULT '',
    year_of_production INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS bom_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL REFERENCES device(id),
    item_number INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    reference_designator TEXT NOT NULL,
    part_value TEXT,
    package TEXT,
    manufacturer TEXT,
    manufacturer_order_code TEXT,
    supplier TEXT,
    supplier_order_code TEXT,
    notes TEXT,
    mounting_type TEXT NOT NULL DEFAULT 'SMT',
    designator_code TEXT,
    eec_category_id INTEGER
);

CREATE TABLE IF NOT EXISTS material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_name TEXT NOT NULL UNIQUE,
    casrn TEXT,
    category TEXT NOT NULL DEFAULT 'element'
);

CREATE TABLE IF NOT EXISTS component_material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bom_entry_id INTEGER NOT NULL REFERENCES bom_entry(id),
    material_id INTEGER NOT NULL REFERENCES material(id),
    mass_mg REAL NOT NULL DEFAULT 0.0,
    note TEXT,
    source_mdf TEXT
);
"""


class Database:
    def __init__(self, config: DatabaseConfig):
        db_path = config.url.replace("sqlite:///", "")
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self):
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def find_or_create_device(self, device: Device) -> int:
        row = self._conn.execute(
            "SELECT id FROM device WHERE model_name = ?",
            (device.model_name,),
        ).fetchone()
        if row:
            return row["id"]

        cur = self._conn.execute(
            "INSERT INTO device (brand, model_name, manufacturer, year_of_production, notes) "
            "VALUES (?, ?, ?, ?, ?)",
            (device.brand, device.model_name, device.manufacturer,
             device.year_of_production, device.notes),
        )
        self._conn.commit()
        return cur.lastrowid

    def insert_bom_entry(self, device_id: int, entry: BOMEntry) -> int | None:
        existing = self._conn.execute(
            "SELECT id FROM bom_entry WHERE device_id = ? AND reference_designator = ?",
            (device_id, entry.reference_designator),
        ).fetchone()
        if existing:
            return None

        cur = self._conn.execute(
            "INSERT INTO bom_entry "
            "(device_id, item_number, quantity, reference_designator, part_value, "
            "package, manufacturer, manufacturer_order_code, supplier, "
            "supplier_order_code, notes, mounting_type, designator_code, eec_category_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (device_id, entry.item_number, entry.quantity,
             entry.reference_designator, entry.part_value, entry.package,
             entry.manufacturer, entry.manufacturer_order_code,
             entry.supplier, entry.supplier_order_code, entry.notes,
             entry.mounting_type, entry.designator_code, entry.eec_category_id),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_device(self, model_name: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM device WHERE model_name = ?",
            (model_name,),
        ).fetchone()
        return dict(row) if row else None

    def get_device_by_id(self, device_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM device WHERE id = ?",
            (device_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_bom_entries(self, device_id: int) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM bom_entry WHERE device_id = ? ORDER BY item_number",
            (device_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def find_bom_entry_by_ref(self, device_id: int, reference: str) -> dict | None:
        """Trova una BOMEntry del device che contiene il reference (anche in un gruppo)."""
        reference = (reference or "").strip()
        if not reference:
            return None
        for row in self._conn.execute(
            "SELECT * FROM bom_entry WHERE device_id = ?", (device_id,)
        ):
            des = row["reference_designator"]
            parts = [d.strip() for d in des.split(",")]
            if des == reference or reference in parts:
                return dict(row)
        return None

    def find_bom_entry_by_part_number(self, part_number: str) -> list[dict]:
        """Trova le BOMEntry il cui part number (MPN) matcherà ``part_number``.

        Confronto best-effort sui campi ``manufacturer_order_code``,
        ``part_value`` e ``supplier_order_code`` con una normalizzazione
        (maiuscolo, spazi e trattini rimossi). Supporta anche part number
        incorporati nel ``part_value`` (es. "2u2-GRM188R61E225MA12D").
        """
        target = _normalize_part(part_number)
        if not target:
            return []
        matches: list[dict] = []
        for row in self._conn.execute("SELECT * FROM bom_entry").fetchall():
            for field in ("manufacturer_order_code", "part_value", "supplier_order_code"):
                value = _normalize_part(row[field])
                if not value:
                    continue
                if value == target or value in target or target in value:
                    matches.append(dict(row))
                    break
        return matches

    def insert_material(self, material: Material) -> int | None:
        """Inserisce un materiale (per material_name univoco). Ritorna id o None se duplicato."""
        existing = self._conn.execute(
            "SELECT id FROM material WHERE material_name = ?",
            (material.material_name,),
        ).fetchone()
        if existing:
            return None

        cur = self._conn.execute(
            "INSERT INTO material (material_name, casrn, category) VALUES (?, ?, ?)",
            (material.material_name, material.casrn, material.category),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_material_id(self, material_name: str) -> int | None:
        row = self._conn.execute(
            "SELECT id FROM material WHERE material_name = ?",
            (material_name,),
        ).fetchone()
        return row["id"] if row else None

    def link_material(
        self,
        bom_entry_id: int,
        material_id: int,
        mass_mg: float = 0.0,
        note: str | None = None,
        source_mdf: str | None = None,
    ) -> int | None:
        """Collega un materiale a una BOMEntry. Ritorna id o None se già collegato."""
        existing = self._conn.execute(
            "SELECT id FROM component_material WHERE bom_entry_id = ? AND material_id = ?",
            (bom_entry_id, material_id),
        ).fetchone()
        if existing:
            return None

        cur = self._conn.execute(
            "INSERT INTO component_material (bom_entry_id, material_id, mass_mg, note, source_mdf) "
            "VALUES (?, ?, ?, ?, ?)",
            (bom_entry_id, material_id, mass_mg, note, source_mdf),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_materials(self) -> list[dict]:
        """Lista materiali con conteggio di BOMEntry collegate."""
        rows = self._conn.execute(
            "SELECT m.id, m.material_name, m.casrn, m.category, "
            "COUNT(cm.id) AS linked_entries "
            "FROM material m "
            "LEFT JOIN component_material cm ON cm.material_id = m.id "
            "GROUP BY m.id ORDER BY m.material_name"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_component_material_links(self, device_id: int | None = None) -> list[dict]:
        """Link materiale↔BOMEntry (per device se indicato), per la UI/demo.

        Ogni riga: material_name, casrn, category, mass_mg, note, source_mdf,
        bom_entry_id, reference_designator, part_value, device model/brand.
        """
        sql = (
            "SELECT cm.id AS link_id, cm.bom_entry_id, cm.mass_mg, cm.note, cm.source_mdf, "
            "m.material_name, m.casrn, m.category, "
            "be.reference_designator, be.part_value, be.manufacturer, "
            "d.model_name, d.brand "
            "FROM component_material cm "
            "JOIN material m ON m.id = cm.material_id "
            "JOIN bom_entry be ON be.id = cm.bom_entry_id "
            "JOIN device d ON d.id = be.device_id "
        )
        params: tuple = ()
        if device_id is not None:
            sql += "WHERE be.device_id = ? "
            params = (device_id,)
        sql += "ORDER BY m.material_name, d.model_name, be.reference_designator"
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_all_devices(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM device ORDER BY model_name").fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        devices = self._conn.execute("SELECT COUNT(*) as c FROM device").fetchone()["c"]
        entries = self._conn.execute("SELECT COUNT(*) as c FROM bom_entry").fetchone()["c"]
        materials = self._conn.execute("SELECT COUNT(*) as c FROM material").fetchone()["c"]
        return {"devices": devices, "bom_entries": entries, "materials": materials}

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
