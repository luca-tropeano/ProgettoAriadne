"""Parser MDF PDF (Material Data File) — table-based con pdfplumber.

Le Material Declaration dei produttori (KEMET/YAGEO, ZVEI, Analog Devices,
ecc.) sono PDF testuali con tabelle: una riga per sostanza con nome, CAS,
massa e percentuale. pdfplumber estrae le tabelle; questo modulo riconosce la
struttura tipica (riga di header con ``Substance Name``/``Substance`` + ``CAS``
+ colonna peso) e produce una lista **piatta** di ``DeclaredSubstance``, lo
stesso modello già usato per l'XML IPC-1752 Class D.

Layout osservati e supportati:

- **ZVEI / per-componente**: colonne esplicite ``Substance Name``, ``CAS #``,
  ``Weight [mg]``, ``Mass Percent``; la massa totale del componente può essere
  in una tabella metadata (celle ``Mass``/``Unit``).
- **KEMET/YAGEO / per-serie**: colonne ``Substance``, ``Common Name``, ``CAS #``
  e una o più colonne ``Weight (gr)`` (una per variante di taglia); viene scelta
  la colonna di peso a destra del CAS e convertita da grammi a milligrammi.

I CAS placeholder (``system``, ``pseudo substance``, ``-``, vuoto) vengono
ignorati: non sono sostanze dichiarabili. I part number candidati vengono
estratti dal testo (pattern tipo Murata ``GRM...``) per il matching con la BOM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ariadne.ipc1752 import DeclaredSubstance

# CAS RN: NNNNNNN-NN-N (2-7 cifre, 2 cifre, 1 cifra).
_CAS_RE = re.compile(r"^\d{2,7}-\d{1,7}-\d$")

# Pattern di part number noti (Murata GRM, KEMET C/L) per il matching con la BOM.
_MPN_PATTERNS = (
    re.compile(r"\bGRM[A-Z0-9-]{8,}\b"),
    re.compile(r"\bC\d{4}[A-Z0-9-]{5,}\b"),
    re.compile(r"\bL\d{4}[A-Z0-9-]{5,}\b"),
)

# CAS/identificativi segnaposto da scartare.
_PLACEHOLDER_CAS = {"", "-", "system", "pseudo substance", "n.a."}

_UNIT_FACTORS = {"mg": 1.0, "g": 1000.0, "gr": 1000.0}


@dataclass
class PdfMdf:
    """Risultato del parsing di un MDF PDF."""

    component_name: str | None = None
    total_mass_mg: float | None = None
    substances: list[DeclaredSubstance] = field(default_factory=list)
    part_numbers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _to_float(value: str) -> float | None:
    """Converte '0,049' / '11,818' / '6,3' / '99,95' in float (decimale italiano)."""
    text = (value or "").strip()
    if not text:
        return None
    text = text.replace(" ", "").replace("%", "").replace(",", ".")
    if not re.fullmatch(r"\d+(?:\.\d+)?", text):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _cas_from(text: str) -> str | None:
    raw = (text or "").strip()
    if raw.lower() in _PLACEHOLDER_CAS:
        return None
    if _CAS_RE.match(raw):
        return raw
    return None


def _first_weight_column(headers_rows: list[list[str]], ncols: int, after_cas: int | None) -> tuple[int | None, float]:
    """Indice della colonna 'weight' (e fattore→mg) cercando nelle prime righe di header.

    Preferisce una colonna a destra del CAS (peso della sostanza, non della parte).
    """
    best_idx: int | None = None
    for row in headers_rows:
        for i in range(ncols):
            cell = (row[i] if i < len(row) else "") or ""
            if "weight" not in cell.lower():
                continue
            if after_cas is not None and i <= after_cas:
                continue
            if best_idx is None or i < best_idx:
                best_idx = i
    if best_idx is None and after_cas is None:
        for row in headers_rows:
            for i in range(ncols):
                cell = (row[i] if i < len(row) else "") or ""
                if "weight" in cell.lower():
                    return i, _unit_factor(cell)
    unit_factor = 1.0
    if best_idx is not None:
        for row in headers_rows:
            for i in range(ncols):
                cell = (row[i] if i < len(row) else "") or ""
                if i == best_idx and "weight" in cell.lower():
                    unit_factor = _unit_factor(cell)
    return best_idx, unit_factor


def _unit_factor(header_cell: str) -> float:
    low = header_cell.lower()
    for unit, factor in _UNIT_FACTORS.items():
        if unit in low:
            return factor
    return 1.0


def parse_mdf_tables(tables: list[list[list[str]]], all_text: str = "") -> PdfMdf:
    """Parsa le tabelle estratte da pdfplumber (layout ZVEI/KEMET).

    ``tables`` è la lista delle tabelle di tutte le pagine (cellule già splittate
    da ``Page.extract_tables``). ``all_text`` (testo grezzo del PDF) viene usato
    per la ricerca dei part number.
    """
    mdf = PdfMdf()
    header_idx: int | None = None
    col_name = col_cas = col_weight = col_pct = None
    unit_factor = 1.0

    for table in tables:
        if not table:
            continue
        nrows = len(table)
        ncols = max((len(r) for r in table), default=0)

        # 1) Tabella metadata: cerca la massa totale (celle 'Mass'/'Unit').
        for row in table:
            cells = [(c or "").replace("\n", " ").strip() for c in row]
            for i, cell in enumerate(cells):
                if cell.lower() == "mass" and i + 1 < len(cells):
                    value = _to_float(cells[i + 1])
                    if value is not None:
                        mdf.total_mass_mg = value
                elif cell.lower() == "unit" and i + 1 < len(cells) and mdf.total_mass_mg is not None:
                    unit = cells[i + 1].lower().strip()
                    mdf.total_mass_mg *= _UNIT_FACTORS.get(unit, 1.0)

        # 2) Individua la tabella/riga di header delle sostanze.
        found_header_here = False
        for r in range(min(6, nrows)):
            cells = [(c or "").replace("\n", " ").strip() for c in table[r]]
            joined = " ".join(cells).lower()
            if "substance" not in joined or "cas" not in joined:
                continue
            header_idx = r
            found_header_here = True
            col_name = col_cas = None
            for i, cell in enumerate(cells):
                low = cell.lower()
                if col_name is None and low == "substance":
                    col_name = i
                elif col_name is None and "substance" in low and "name" in low:
                    col_name = i
                if col_cas is None and low.startswith("cas"):
                    col_cas = i
            break

        # 3) Righe sostanze: header sulla stessa tabella (colonne peso su righe H..H+2).
        if found_header_here:
            headers_rows = [table[j] for j in range(header_idx, min(header_idx + 3, nrows))]
            col_weight, unit_factor = _first_weight_column(headers_rows, ncols, after_cas=col_cas)
            col_pct = None
            for j in range(header_idx, min(header_idx + 3, nrows)):
                for i, cell in enumerate(table[j] or []):
                    cell_low = (cell or "").lower()
                    if "percent" not in cell_low:
                        continue
                    # percentuali della SOSTANZA: ultima colonna 'percent' (a destra del CAS)
                    if col_pct is None:
                        col_pct = i
                    elif col_cas is None or i > col_cas:
                        col_pct = i

            start = header_idx + 1
            for r in range(start, nrows):
                row = [(c or "").replace("\n", " ").strip() for c in table[r]]
                # può esserci più di una riga di header (es. 'Weight (gr)')
                if col_weight is None and any("weight" in (c or "").lower() for c in row):
                    continue
                sub_name = row[col_name] if col_name is not None and col_name < len(row) else ""
                if not sub_name or "substance" in sub_name.lower():
                    continue
                cas_raw = row[col_cas] if col_cas is not None and col_cas < len(row) else "-"
                cas = _cas_from(cas_raw)
                if cas is None:
                    if cas_raw and cas_raw not in _PLACEHOLDER_CAS:
                        mdf.warnings.append(f"Sostanza '{sub_name}': CAS '{cas_raw}' scartato")
                    continue
                mass_mg: float | None = None
                if col_weight is not None and col_weight < len(row):
                    w = _to_float(row[col_weight])
                    if w is not None:
                        mass_mg = round(w * unit_factor, 6)
                pct = _parse_pct(row[col_pct]) if col_pct is not None and col_pct < len(row) else None
                if mass_mg is None and pct is None:
                    continue
                mdf.substances.append(
                    DeclaredSubstance(name=sub_name, cas=cas, mass_mg=mass_mg, concentration_pct=pct)
                )

    # 4) Component name: prima cella della prima riga dati della tabella sostanze.
    for table in tables:
        if not table:
            continue
        for r in range(min(6, len(table))):
            cells = [(c or "").replace("\n", " ").strip() for c in table[r]]
            joined = " ".join(cells).lower()
            if "substance" in joined and "cas" in joined and r + 1 < len(table):
                first_cell = ((table[r + 1][0] if table[r + 1] else "") or "").replace("\n", " ").strip()
                if first_cell:
                    mdf.component_name = first_cell
                    break
        if mdf.component_name:
            break

    # 5) Part number candidati (per il matching con la BOM).
    if all_text:
        seen: set[str] = set()
        for pat in _MPN_PATTERNS:
            for match in pat.finditer(all_text):
                token = match.group(0)
                if token not in seen:
                    seen.add(token)
                    mdf.part_numbers.append(token)

    mdf.substances = _merge_duplicate_substances(mdf.substances)
    return mdf


def _merge_duplicate_substances(subs: list[DeclaredSubstance]) -> list[DeclaredSubstance]:
    """Fonde le righe con la stessa sostanza (nome+CAS) sommando le masse."""
    merged: dict[tuple[str, str], DeclaredSubstance] = {}
    for s in subs:
        key = (s.name, s.cas)
        if key in merged:
            prev = merged[key]
            if s.mass_mg is not None:
                prev.mass_mg = round((prev.mass_mg or 0) + s.mass_mg, 6)
            if s.concentration_pct is not None:
                prev.concentration_pct = max(prev.concentration_pct or 0, s.concentration_pct)
        else:
            merged[key] = DeclaredSubstance(
                name=s.name, cas=s.cas, mass_mg=s.mass_mg, concentration_pct=s.concentration_pct
            )
    return list(merged.values())


def _parse_pct(text: str) -> float | None:
    pct_text = (text or "").strip()
    if not pct_text:
        return None
    if "rest" in pct_text.lower():
        return None
    if re.search(r"\d\s*-\s*\d", pct_text):
        numbers = [_to_float(x) for x in re.split(r"\s*-\s*", pct_text)]
        numbers = [n for n in numbers if n is not None]
        return max(numbers) if numbers else None
    return _to_float(pct_text)


def parse_pdf_mdf(path: str | Path) -> PdfMdf:
    """Estrae le tabelle dal PDF con pdfplumber e le parsa come MDF."""
    import pdfplumber

    tables: list[list[list[str]]] = []
    all_text_parts: list[str] = []
    with pdfplumber.open(path) as doc:
        for page in doc.pages:
            t = page.extract_tables()
            if t:
                tables.extend(t)
            text = page.extract_text() or ""
            if text:
                all_text_parts.append(text)
    return parse_mdf_tables(tables, all_text="\n".join(all_text_parts))