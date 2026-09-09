"""Downloader MDF (Material Data File) dai portali pubblici — percorso ONLINE.

I produttori/distributori non espongono un'API documentata per le "Material
Composition Declarations" (IPC-1752). Questo modulo lavora per "harvest"
deterministico e dimostrabile:

1. costruisce le URL di ricerca dei portali per il part number;
2. scarica la pagina e ne estrae i link candidati (pattern tipici dei documenti
   ambientali: ipc / 1752 / mcd / material / composition / declaration / rohs
   / reach, estensione xml/pdf/csv/zip);
3. scarica i candidati XML e prova a parsarli come IPC-1752A/B Class D
   (il parse È la validazione);
4. salva localmente il primo XML valido.

Il client HTTP è iniettabile (parametro ``client``) così i test possono operare
senza rete con un oggetto duck-typed con interfaccia ``.get(url)`` che ritorna
una risposta con ``.text`` e ``.raise_for_status()``.

La demo resta 100% offline: questo percorso è opzionale, invocato dal CLI
``mdf-download``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin

# Portali e URL di ricerca costruiti per part number (ordine di tentativo).
SEARCH_URLS = {
    "murata": "https://www.murata.com/en-global/search/productsearch?partno={part}",
    "digikey": "https://www.digikey.com/en/products/result?keywords={part}",
    "mouser": "https://www.mouser.com/c/?q={part}",
    "bomcheck": "https://www.bomcheck.net/en/Search?q={part}",
    "octopart": "https://octopart.com/search?q={part}",
}

# Parole chiave che fanno sospettare un link a un documento dei materiali.
_LINK_HINTS = (
    "ipc",
    "1752",
    "rohs",
    "mcd",
    "svhc",
    "reach",
    "declaration",
    "material",
    "composition",
    "environment",
    "compliance",
)

_DOC_EXT = (".xml", ".pdf", ".csv", ".zip")


@dataclass
class DownloadResult:
    part_number: str
    downloaded: Path | None = None
    found: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class MDFPortalDownloader:
    def __init__(self, client=None, max_candidates: int = 12, timeout: float = 20.0):
        import httpx

        if client is None:
            self._owns_client = True
            self._client = httpx.Client(follow_redirects=True, timeout=timeout)
        else:
            self._owns_client = False
            self._client = client
        self._max_candidates = max_candidates

    # --------------------------------------------------------------- HTTP

    def _get_text(self, url: str) -> str:
        resp = self._client.get(url)
        resp.raise_for_status()
        return getattr(resp, "text", "") or ""

    # ---------------------------------------------------------- harvesting

    def _candidate_links(self, page_html: str, base_url: str) -> list[str]:
        """Estrae dai link della pagina quelli che sembrano documenti MDF."""
        found: dict[str, int] = {}
        pattern = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
        for match in pattern.finditer(page_html):
            href = match.group(1).strip()
            text = re.sub(r"<[^>]+>", "", match.group(2)).lower()
            url = urljoin(base_url, href)
            if not (url.startswith("http://") or url.startswith("https://")):
                continue
            hay = f"{url.lower()} {text}"
            score = sum(1 for hint in _LINK_HINTS if hint in hay)
            if score == 0:
                continue
            ext = Path(url.split("?", 1)[0]).suffix.lower()
            if ext not in _DOC_EXT:
                continue
            if url not in found or score > found[url]:
                found[url] = score
        ranked = sorted(found, key=found.get, reverse=True)
        return ranked[: self._max_candidates]

    def _build_search_urls(self, part_number: str, source: str) -> list[str]:
        if source == "auto":
            return [url.format(part=part_number) for url in SEARCH_URLS.values()]
        if source.startswith("url:"):
            custom = source[len("url:"):]
            if custom.startswith(("http://", "https://")):
                return [custom]
            raise ValueError(f"source 'url:' non è un URL valido: {custom}")
        if source in SEARCH_URLS:
            return [SEARCH_URLS[source].format(part=part_number)]
        raise ValueError(
            f"source sconosciuto: {source} "
            f"(auto|{'|'.join(SEARCH_URLS)}|url:https://...)"
        )

    # ----------------------------------------------------------- download

    def download(self, part_number: str, out_dir: str = "mdf_downloads",
                 source: str = "auto") -> DownloadResult:
        result = DownloadResult(part_number=part_number)
        out = Path(out_dir)

        try:
            search_urls = self._build_search_urls(part_number, source)
        except ValueError as e:
            result.errors.append(str(e))
            return result

        for search_url in search_urls:
            if result.downloaded is not None:
                break
            try:
                html = self._get_text(search_url)
            except Exception as e:
                result.errors.append(f"{search_url}: {e}")
                continue

            for url in self._candidate_links(html, search_url):
                if not url.lower().endswith(".xml"):
                    # documento candidato ma non parsabile (pdf/csv/zip)
                    result.found.append(url)
                    continue
                from ariadne.ipc1752 import parse_class_d_xml

                try:
                    body = self._get_text(url)
                    products = parse_class_d_xml(body)
                except Exception:
                    result.found.append(url)
                    continue
                if not products:
                    result.found.append(url)
                    continue
                out.mkdir(parents=True, exist_ok=True)
                dest = out / f"{part_number}_mdf.xml"
                dest.write_text(body, encoding="utf-8")
                result.downloaded = dest
                break

        return result

    def close(self):
        if self._owns_client:
            self._client.close()