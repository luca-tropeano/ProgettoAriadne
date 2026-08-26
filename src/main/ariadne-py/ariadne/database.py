from __future__ import annotations

import sqlite3
from pathlib import Path

from ariadne.config import DatabaseConfig
from ariadne.models import BOMEntry, Device, ImportResult

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
