from __future__ import annotations

import openpyxl

from ariadne.models import BOMEntry


EXCEL_HEADER_ROW = 6


def _detect_mounting_type(package: str | None) -> str:
    if not package:
        return "SMT"
    upper = package.strip().upper()
    if upper.startswith("DIP") or upper.startswith("SIP") or upper.startswith("TO-"):
        return "THT"
    return "SMT"


def parse_excel_bom(file_path: str) -> list[BOMEntry]:
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    entries = []

    for row in ws.iter_rows(min_row=EXCEL_HEADER_ROW + 1, values_only=False):
        item_text = row[0].value
        if item_text is None:
            continue
        try:
            item_number = int(item_text)
        except (ValueError, TypeError):
            continue

        quantity_text = row[1].value
        try:
            quantity = int(quantity_text)
        except (ValueError, TypeError):
            continue

        reference = row[2].value
        if not reference:
            continue

        def _str(val):
            return str(val) if val is not None else None

        package = _str(row[8].value if len(row) > 8 else None)

        entries.append(BOMEntry(
            item_number=item_number,
            quantity=quantity,
            reference_designator=str(reference),
            part_value=_str(row[4].value if len(row) > 4 else None),
            package=package,
            manufacturer=_str(row[9].value if len(row) > 9 else None),
            manufacturer_order_code=_str(row[10].value if len(row) > 10 else None),
            supplier=_str(row[12].value if len(row) > 12 else None),
            supplier_order_code=_str(row[13].value if len(row) > 13 else None),
            notes=_str(row[11].value if len(row) > 11 else None),
            mounting_type=_detect_mounting_type(package),
        ))

    wb.close()
    return entries
