from __future__ import annotations

import re

from ariadne.models import BOMEntry

RE_DESIGNATOR = re.compile(r"\b[A-Z]{1,3}\d+\b")
RE_ITEM_NUMBER = re.compile(r"^\s*(\d{1,4})\s")
RE_QTY_X = re.compile(r"\b(\d+)\s*x\s*", re.IGNORECASE)
RE_VALUE_WITH_UNIT = re.compile(r"\b(\d+\.?\d*\s*(?:p[FP]?|n[FP]?|u[FP]?|m[FP]?|k|M|G|Ω|Ω|ohm|F|H|Hz|V|A|W|%|R)\b)", re.IGNORECASE)
RE_VALUE_SHORT = re.compile(r"\b(\d+(?:[kKMGTPEuunmp])\d*)\b")
RE_MFR_KNOWN = re.compile(
    r"\b(STMICROELECTRONICS|KEMET|PANASONIC|BOURNS|AVAGO|WURTH|NDK|MURATA|TDK|YAGEO|VISHAY|ONSEMI|NXP|INFINEON|DIODES|MAXIM|ANALOG|MICROCHIP|SAMSUNG|SANYO|NICHICON|ROHM)\b",
    re.IGNORECASE,
)
_PACKAGE_SET = {
    "0603", "0603C", "0603R", "0603L", "0805", "0805C", "0805R",
    "1206", "1206C", "1206R", "1210", "1812", "2010", "2512",
    "0402", "0201", "01005",
    "SOT23", "SOT323", "SOT89", "SOT223", "SOT-23", "SOT-323",
    "SOD123", "SOD323", "SOD523", "SOD128", "SOD-123", "SOD-323",
    "SOP8", "SOP16", "SOIC8", "SOIC16", "SOIC-8", "SOIC-16",
    "TSSOP14", "TSSOP20", "TSSOP-14", "QFN", "QFN48", "QFN32",
    "QFP", "QFP48", "QFP64", "LQFP48", "LQFP64", "LQFP100",
    "VFQFPN48", "VFQFPN32", "BGA", "BGA100", "BGA256",
    "PLCC4", "PLCC20", "PLCC44", "PLCC84",
    "DPAK", "D2PAK", "TO-92", "TO-220", "TO-247", "TO-252",
    "DPAK-3", "DPAK-5",
    "SMD", "MELF", "LED", "PAD_4x4", "PAD",
    "1515L", "NR4012", "2917C",
    "SOD-323-2", "SOT-23-3", "SOT-23-5", "SOT-23-6",
    "TSSOP-14", "SOP-16",
    "VQFN-49",
    "M4_DIODA",
    "HEADER_MALE_1X1_INKPLATE",
    "CR2032-BS-6-1",
    "STANDOFF_M3",
    "U262-161N-4BVC11",
    "WP27D-S050VA3-R15000",
    "JST-2PIN-SMD",
    "HYC77-TF09-200",
    "K2-1114SA-A4SW-06",
    "SK-3296S-01-L1",
    "YTSA007A0151803B",
    "EASYC-SMD",
    "EASYC-CONNECTOR",
    "ABS07AIG-32.768KHZ-7-D-T",
    "7LC32768F12UC",
    "PCF85063A",
    "SN74LVC1G34DBV",
    "ED052TC4",
    "TPS7A2633DRVR",
    "MCP73831T",
    "MC14093BDTR2G",
    "PCAL6416AHF,128",
    "TPS3840PL27DBVR",
    "LTST-S270GKT",
    "SMD_JUMPER",
    "SMD_JUMPER_3_PAD_CONNECTED_LEFT_TRACE",
    "SMD-JUMPER-CONNECTED_TRACE_SOLDERMASK",
    "TEST_POINT_SMD_0.8MM",
    "0603C", "0805C", "1206C", "0603R", "0805R", "1206R",
}


def _detect_mounting_type(package: str | None) -> str:
    if not package:
        return "SMT"
    upper = package.strip().upper()
    if upper.startswith("DIP") or upper.startswith("SIP") or upper.startswith("TO-"):
        return "THT"
    return "SMT"


def _is_designator_list(text: str) -> bool:
    return bool(re.match(r"^[A-Z]{1,3}\d+(?:,[A-Z]{1,3}\d+)*$", text))


def _is_package(text: str) -> bool:
    upper = text.upper()
    if re.match(r"^\d{3,4}[A-Z]?$", upper):
        return True
    if re.match(r"^[A-Z]+-\d+$", upper):
        return True
    if re.match(r"^(?:SOT|SOD|SOP|SOIC|QFN|QFP|BGA|LQFP|VFQFPN|PLCC|PGA|DPAK|D2PAK|TO-\d+|DIP|SIP|LED|MELF|PAD)", upper):
        return True
    return False


def _is_package_name(word: str) -> bool:
    return word.upper() in _PACKAGE_SET or bool(re.match(r"^(?:SOT|SOD|SOP|SOIC|QFN|QFP|BGA|LQFP|VFQFPN|PLCC|PGA|DPAK|TO-|DIP|SIP)\d*", word, re.IGNORECASE))


def _looks_like_designator(word: str, line: str) -> bool:
    m = re.search(r"\b" + re.escape(word) + r"\b", line)
    if not m:
        return False
    end = m.end()
    if end < len(line):
        rest = line[end:]
        if re.match(r"^\.\d", rest):
            return False
    return True


def parse_pdf_bom_text(text: str) -> list[BOMEntry]:
    raw = [l.strip() for l in text.split("\n") if l.strip()]
    lines = []
    for line in raw:
        if line.startswith("--- Page") or line.startswith("Page "):
            continue
        if re.match(r"^\s*(?:Item|Qty|Ref|Designat|Package|Quantity|Value|Part|Suppl|Manufacturer|Id|Desc|Q\.ty)\b", line, re.IGNORECASE):
            continue
        if lines and not re.match(r"^\d", line):
            lines[-1] += " " + line
        else:
            lines.append(line)

    entries = []
    item_counter = 0
    seen_refs = set()

    for line in lines:
        designators_raw = RE_DESIGNATOR.findall(line)
        designators_raw = [d for d in designators_raw if not _is_package_name(d) and _looks_like_designator(d, line)]
        if not designators_raw:
            continue

        designators = sorted(set(designators_raw), key=lambda x: (x[0], int(x[1:]) if x[1:].isdigit() else 0))
        ref = ",".join(designators)
        if ref in seen_refs:
            continue
        seen_refs.add(ref)

        tokens = [t for t in re.split(r"\s{2,}|\t", line) if t.strip()]
        if len(tokens) < 3:
            tokens = line.split()

        numbers = [int(t) for t in tokens if t.strip().isdigit()]

        item_number = numbers[0] if numbers else None
        quantity = 1
        if numbers:
            candidates = [n for n in numbers if n != item_number and 1 <= n <= 9999]
            if candidates:
                quantity = candidates[0]

        qty_x = RE_QTY_X.search(line)
        if qty_x:
            quantity = int(qty_x.group(1))

        part_value = None
        manufacturer = None
        package = None

        for t in tokens:
            token = t.strip()
            if not token or token.isdigit():
                continue
            if token == ref:
                continue
            if _is_designator_list(token):
                continue

            if _is_package(token) and package is None:
                package = token
                continue

            m = RE_MFR_KNOWN.match(token)
            if m and manufacturer is None:
                manufacturer = m.group(1).upper()
                continue

            if part_value is None:
                vm = RE_VALUE_WITH_UNIT.search(token)
                if vm:
                    part_value = vm.group(1)
                else:
                    vs = RE_VALUE_SHORT.search(token)
                    if vs:
                        part_value = vs.group(1)

        if part_value is None:
            vm = RE_VALUE_WITH_UNIT.search(line)
            if vm:
                part_value = vm.group(1)
            else:
                vs = RE_VALUE_SHORT.search(line)
                if vs:
                    part_value = vs.group(1)

        if part_value is None:
            for t in tokens:
                token = t.strip()
                if _is_package_name(token) or RE_MFR_KNOWN.match(token):
                    continue
                if token.isdigit() or re.match(r"^\d{1,2}$", token):
                    continue
                if _is_designator_list(token):
                    continue
                if len(token) >= 3:
                    part_value = token
                    break

        if manufacturer is None:
            m = RE_MFR_KNOWN.search(line)
            if m:
                manufacturer = m.group(1).upper()

        if package is None:
            for t in tokens:
                if _is_package(t.strip()):
                    package = t.strip()
                    break

        item_counter += 1
        if item_number is None:
            item_number = item_counter

        entries.append(BOMEntry(
            item_number=item_number,
            quantity=quantity,
            reference_designator=ref,
            part_value=part_value,
            manufacturer=manufacturer,
            package=package,
            mounting_type=_detect_mounting_type(package),
        ))

    return entries
