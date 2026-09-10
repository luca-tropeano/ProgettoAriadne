"""Regole deterministiche di sourcing MDF per componente.

Classifica una coppia (produttore, part number) in:

- ``family_mcd`` — esiste una Material Composition Declaration per-famiglia
  scaricata localmente (``test_data/mdf/MCD-Ceramic.pdf`` per KEMET/YAGEO
  MLCC SMD, ``mdf_kemet_c4ak_film.pdf`` per il film DC-link, ...). La
  dichiarazione è per-serie: i materiali coprono tutti i part della famiglia.
- ``reference`` — nessun MDF pubblico deterministico: si rimanda alla pagina
  ufficiale di conformità/MDF del produttore.
- ``no_mpn`` — part number generico/assente: nessuna fonte ricercabile.

Le stesse regole alimentano sia ``scripts/mdf_finder.py`` (report statico)
sia ``ariadne.mdf_auto.auto_source_mdf`` (sourcing automatico all'import della
BOM).
"""

from __future__ import annotations

import re
from pathlib import Path

# test_data/mdf relativo alla root del progetto (ariadne-py).
BASE_DIR = Path(__file__).resolve().parent.parent
MDF_DIR = BASE_DIR / "test_data" / "mdf"

_KEMET_MLCC = re.compile(r"^C\d{4}C\d{3}", re.IGNORECASE)   # C0603C104K5RACTU
_YAGEO_MLCC = re.compile(r"^CC\d{4}", re.IGNORECASE)        # CC1206KKX7R8BB225
_KEMET_FILM = re.compile(r"^C4AK", re.IGNORECASE)           # C4AK… (film DC-link)

_MPN_MANUFACTURER_HINT: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^RC\d{4}"), "YAGEO"),   # serie YAGEO RC (thick film)
    (re.compile(r"^PE\d{4}"), "YAGEO"),   # PE2512 current sense
]

_MANUF_ALIASES = {
    "KEMET OR GENERIC": "KEMET",
    "YAGEO OR GENERIC": "YAGEO",
    "ON SEMI": "ON SEMICONDUCTOR",
    "ONSEMI": "ON SEMICONDUCTOR",
    "ST MICROELECTRONICS": "STMICROELECTRONICS",
    "WURTH ELECTRONIK": "WURTH ELEKTRONIK",
}

# Pagina ufficiale conformità/MDF per produttore (chiavi normalizzate).
REFERENCE_URLS: dict[str, str] = {
    "KEMET": "https://yageogroup.com/About/Sustainability/Environment/KemetFocus",
    "YAGEO": "https://yageogroup.com/About/Sustainability/Resources",
    "AVX": "https://connect.kyocera-avx.com/compliance/",
    "TDK": "https://product.tdk.com/en/environment/index.html",
    "MURATA": "https://www.murata.com/en-us/support/regulation",
    "TEXAS INSTRUMENTS": "https://www.ti.com/materialcontent/home",
    "MICROCHIP": "https://www.microchip.com/en-us/support/quality-and-environmental-compliance",
    "NXP": "https://www.nxp.com/support/documents/quality/environmental-information:ENVTQ",
    "STMICROELECTRONICS": "https://www.st.com/en/about-us/environmental-information.html",
    "WURTH ELEKTRONIK": "https://www.we-online.com/en/service/quality",
    "PANASONIC": "https://industrial.panasonic.com/ww/eco/compliance",
    "VISHAY": "https://www.vishay.com/environmental/",
    "ROHM": "https://www.rohm.com/quality-and-environment",
    "DIODES": "https://www.diodes.com/quality/quality-and-environmental/",
    "BOURNS": "https://www.bourns.com/support/rohs-compliance",
    "LITTELFUSE": "https://www.littelfuse.com/quality/substance-compliance.aspx",
    "MOLEX": "https://www.molex.com/en-us/company/compliance",
    "AMPHENOL": "https://www.amphenol.com/environmental-resources",
    "ON SEMICONDUCTOR": "https://www.onsemi.com/design/support/quality/environmental",
    "SILICON LABS": "https://www.silabs.com/environmental",
    "MAXIM": "https://www.analog.com/en/about-adi/quality/environmental-compliance.html",
    "ANALOG DEVICES": "https://www.analog.com/en/about-adi/quality/environmental-compliance.html",
    "TOSHIBA": "https://toshiba.semicon-storage.com/eu/semiconductor/company/environment.html",
    "NEXPERIA": "https://www.nexperia.com/about/quality/environmental-information.html",
    "SUSUMU": "https://www.susumu.co.jp/english/environment/",
    "COILCRAFT": "https://www.coilcraft.com/en-us/resources/quality/",
    "FAIRCHILD SEMICONDUCTOR": "https://www.onsemi.com/design/support/quality/environmental",
    "AVAGO": "https://www.broadcom.com/products/technology/environmental-resources",
    "HARWIN": "https://www.harwin.com/quality-and-environment/",
    "TE": "https://www.te.com/en/about-te/sustainability.html",
    "ECS": "https://ecsxtal.com/support/env-compliance/",
    "EPSON": "https://global.epson.com/company/environment/",
    "TXC": "https://www.txccrystal.com/quality",
    "ABRACON": "https://abracon.com/support/rohs-reach/",
    "PULSE ELECTRONICS": "https://www.pulseelectronics.com/about-us/quality",
    "NDK": "https://www.ndk.co.jp/en/environment/",
    "ADESTO": "https://www.renesas.com/en/about/resources/environmental",
    "MULTICOMP": "https://export.farnell.com/",
    "WALSIN": "https://www.walsin.com/system/quality.html",
    "BOURNS INC": "https://www.bourns.com/support/rohs-compliance",
}

_GENERIC_MPNS = {
    "", "NO COMPONENTS", "NOT_POPULATED_0603", "NOT_POPULATED",
    "DNF", "NP", "N.A.", "NONE", "NEEDLE-PAD-1.7MM", "NETS_L1_W0.5",
    "PCB GZ REV2 - 2 LAYERS", "TP SMD-1MM",
}


def normalize_manufacturer(name: str) -> str:
    """Nome produttore normalizzato (upper, alias verso la chiave canonica)."""
    raw = re.sub(r"\s+", " ", (name or "").strip().upper())
    return _MANUF_ALIASES.get(raw, raw)


def has_usable_mpn(mpn: str) -> bool:
    return (mpn or "").strip().upper() not in _GENERIC_MPNS


def family_mcd_file(manufacturer: str, mpn: str) -> str:
    """Nome del file MCD per-famiglia che copre (produttore, mpn), o ''. """
    man = normalize_manufacturer(manufacturer)
    mpn = (mpn or "").strip()
    if man == "KEMET" and _KEMET_MLCC.match(mpn):
        return "MCD-Ceramic.pdf"
    if man == "YAGEO" and _YAGEO_MLCC.match(mpn):
        return "MCD-Ceramic.pdf"
    if man == "KEMET" and _KEMET_FILM.match(mpn):
        return "mdf_kemet_c4ak_film.pdf"
    return ""


def reference_url(manufacturer: str, mpn: str = "") -> str:
    """URL ufficiale di conformità/MDF del produttore, o ''. """
    man = normalize_manufacturer(manufacturer)
    if not man and mpn:
        for pat, hint in _MPN_MANUFACTURER_HINT:
            if pat.match((mpn or "").strip()):
                man = hint
                break
    return REFERENCE_URLS.get(man, "")


def classify(manufacturer: str, mpn: str) -> dict:
    """Classifica (produttore, mpn) → dict {status, mdf_file, reference_url, note}.

    ``manufacturer`` può venire "corretto" in presenza di part number riconoscibili
    (es. RC…/PE… → YAGEO) e viene restituito nel campo ``manufacturer``.
    """
    man = normalize_manufacturer(manufacturer)
    mpn = (mpn or "").strip()

    if man in {"YAGEO", "N.A.", ""}:
        for pat, hint in _MPN_MANUFACTURER_HINT:
            if pat.match(mpn):
                man = hint
                break

    url = REFERENCE_URLS.get(man, "")

    if not has_usable_mpn(mpn):
        return {
            "status": "no_mpn",
            "manufacturer": man,
            "mpn": mpn,
            "mdf_file": "",
            "reference_url": "",
            "note": "componente generico/DNF senza part number ricercabile",
        }

    file = family_mcd_file(man, mpn)
    if file:
        return {
            "status": "family_mcd",
            "manufacturer": man,
            "mpn": mpn,
            "mdf_file": file,
            "reference_url": url,
            "note": (
                f"Material Composition Declaration per-serie "
                f"({file}) — materials di famiglia, non per singolo part"
            ),
        }

    return {
        "status": "reference",
        "manufacturer": man,
        "mpn": mpn,
        "mdf_file": "",
        "reference_url": url,
        "note": (
            "nessun MDF pubblico deterministico; richiedere la dichiarazione "
            "al produttore o usare la pagina di conformita'"
        ),
    }