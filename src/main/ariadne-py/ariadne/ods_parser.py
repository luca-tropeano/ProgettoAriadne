"""Parser per BOM in formato OpenDocument Spreadsheet (.ods).

Schema dinamico: individua la riga di intestazione per nome delle colonne
(Ref/Qty/Value/Footprint/Description/Manufacturer/...) e mappa le celle
corrispondenti, gestendo anche righe di titolo/meta sopra l'header.
"""

from __future__ import annotations

from pathlib import Path

from odf.opendocument import load
from odf.table import Table, TableCell, TableRow
from odf.text import P

from ariadne.models import BOMEntry


# Alias normalizzati dei nomi colonna -> attributo BOMEntry
_COLUMN_ALIASES = {
    "ref": "reference_designator",
    "reference": "reference_designator",
    "designator": "reference_designator",
    "refdes": "reference_designator",
    "qty": "quantity",
    "quantity": "quantity",
    "value": "part_value",
    "designation": "part_value",
    "part": "part_value",
    "part/value": "part_value",
    "footprint": "package",
    "package": "package",
    "foot print": "package",
    "manufacturer": "manufacturer",
    "mfr": "manufacturer",
    "description": "notes",
    "supplier": "supplier",
    "vendor": "supplier",
    "supplier and ref": "supplier",
    "manufacturer part number": "manufacturer_order_code",
    "mfr part number": "manufacturer_order_code",
    "mpn": "manufacturer_order_code",
    "supplier part number": "supplier_order_code",
    "supplier order code": "supplier_order_code",
    "mouserpn": "supplier_order_code",
    "mouser_pn": "supplier_order_code",
}


def _cell_text(cell: TableCell) -> str:
    if cell is None:
        return ""
    parts = []
    for p in cell.getElementsByType(P):
        parts.append(str(p))
    return " ".join(parts).strip()


def _row_cells(row: TableRow):
    cells = []
    for cell in row.getElementsByType(TableCell):
        cells.append(cell)
    return cells


def _expand_repeated(cells) -> list[TableCell | None]:
    """Esplode le celle con 'number columns repeated' per riempire gli spazi vuoti."""
    out: list[TableCell | None] = []
    for cell in cells:
        repeat = int(cell.getAttribute("numbercolumnsrepeated") or 1) if cell is not None else 1
        for _ in range(min(repeat, 1000)):
            out.append(cell if cell is not None and _cell_text(cell) else None)
    return out


def _column_names(row: TableRow) -> list[str]:
    names = []
    for cell in _expand_repeated(_row_cells(row)):
        t = _cell_text(cell).strip().lower()
        names.append(t)
    return names


def _is_header_row(names: list[str]) -> bool:
    keys = {n for n in names if n}
    return ("ref" in keys or "reference" in keys or "designator" in keys or "refdes" in keys) and (
        "qty" in keys or "quantity" in keys
    )


def _mapping_from_header(names: list[str]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for idx, name in enumerate(names):
        target = _COLUMN_ALIASES.get(name)
        if target and target not in mapping:
            mapping[target] = idx
    return mapping


def _detect_mounting_type(package: str) -> str:
    pkg = (package or "").upper()
    for prefix in ("DIP", "SIP", "TO-", "TO92", "DO-35", "DO-41", "RAXIAL", "CP_RADIAL", "C_RECT"):
        if pkg.startswith(prefix) or prefix in pkg:
            return "THT"
    if "THT" in pkg or "TH_" in pkg or "PTH" in pkg or "HORIZONTAL" in pkg or "VERTICAL" in pkg:
        return "THT"
    if "SMD" in pkg or "SM_" in pkg or "SMT" in pkg or "QFP" in pkg or "SOT" in pkg or "0603" in pkg or "0805" in pkg or "1206" in pkg:
        return "SMT"
    return "SMT"


def parse_ods_bom(file_path: str) -> list[BOMEntry]:
    path = Path(file_path)
    doc = load(str(path))
    tables = doc.spreadsheet.getElementsByType(Table)
    if not tables:
        return []

    header_row_idx = None
    header_names: list[str] = []
    all_rows: list[list[TableCell | None]] = []

    for table in tables:
        rows = table.getElementsByType(TableRow)
        for i, row in enumerate(rows):
            cells = _expand_repeated(_row_cells(row))
            all_rows.append(cells)
            if header_row_idx is None:
                names = _column_names(row)
                if _is_header_row(names):
                    header_row_idx = len(all_rows) - 1
                    header_names = names

    if header_row_idx is None:
        return []

    mapping = _mapping_from_header(header_names)
    ref_idx = mapping.get("reference_designator")
    qty_idx = mapping.get("quantity")
    if ref_idx is None or qty_idx is None:
        return []

    entries = []
    item_number = 0

    for cells in all_rows[header_row_idx + 1:]:
        def _val(idx):
            if idx is None or idx >= len(cells) or cells[idx] is None:
                return None
            v = _cell_text(cells[idx])
            return v if v else None

        ref_text = _val(ref_idx)
        qty_text = _val(qty_idx)
        if not ref_text or not qty_text:
            continue
        try:
            quantity = int(qty_text)
        except (ValueError, TypeError):
            continue

        designators = ",".join(d for d in ref_text.replace(";", ",").split(",") if d.strip())
        if not designators:
            continue

        package = _val(mapping.get("package"))
        entry = BOMEntry(
            item_number=item_number + 1,
            quantity=quantity,
            reference_designator=designators,
            part_value=_val(mapping.get("part_value")),
            package=package,
            mounting_type=_detect_mounting_type(package or ""),
            manufacturer=_val(mapping.get("manufacturer")),
            manufacturer_order_code=_val(mapping.get("manufacturer_order_code")),
            supplier=_val(mapping.get("supplier")),
            supplier_order_code=_val(mapping.get("supplier_order_code")),
            notes=_val(mapping.get("notes")),
        )
        entries.append(entry)
        item_number += 1

    return entries
