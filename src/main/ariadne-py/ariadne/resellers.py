"""Link a distributori ufficiali per un part number (MPN).

Genera URL di ricerca dei principali rivenditori/mercati componente:
DigiKey, Mouser, Farnell, RS e Octopart (aggregatore). Usati nella web UI
per collegare ogni componente che ha un codice identificativo.
"""

from __future__ import annotations

from urllib.parse import quote

_DISTRIBUTORS: list[tuple[str, str]] = [
    ("DigiKey", "https://www.digikey.it/it/products/result?keywords={q}"),
    ("Mouser", "https://www.mouser.it/search/Refine.aspx?Keyword={q}"),
    ("Farnell", "https://it.farnell.com/search?st={q}"),
    ("RS", "https://it.rs-online.com/web/c/?searchTerm={q}"),
    ("Octopart", "https://octopart.com/search?q={q}"),
]


def reseller_links(part_number: str | None) -> list[dict]:
    """Link di ricerca per un MPN; lista vuota se non c'è codice identificativo."""
    part_number = (part_number or "").strip()
    if not part_number:
        return []
    q = quote(part_number, safe="")
    return [{"name": name, "url": url.format(q=q)} for name, url in _DISTRIBUTORS]