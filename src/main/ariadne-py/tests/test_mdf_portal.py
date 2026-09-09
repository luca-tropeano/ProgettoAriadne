from __future__ import annotations

from ariadne.mdf_portal import MDFPortalDownloader, SEARCH_URLS

PART = "GRM188R61E225MA12D"

CLASS_D_XML = (
    '<MainDeclaration xmlns="http://webstds.ipc.org/175x/2.0" version="2.0">'
    '<Product unitType="Each"><ProductID itemNumber="GRM188R61E225MA12D"/>'
    '<MaterialInfo><HomogeneousMaterialList>'
    '<HomogeneousMaterial name="Ceramic" materialGroupName="Ceramic">'
    '<Amount value="5.2" UOM="mg"/>'
    '<SubstanceCategoryList><SubstanceCategory name="Supplier">'
    '<Substance name="Barium titanate"><SubstanceID identity="12047-27-7" authority="CAS"/>'
    '<Concentration value="86.27"/></Substance>'
    '</SubstanceCategory></SubstanceCategoryList></HomogeneousMaterial>'
    '</HomogeneousMaterialList></MaterialInfo></Product></MainDeclaration>'
)


class FakeResp:
    def __init__(self, text: str = "", status: int = 200):
        self.text = text
        self._status = status

    def raise_for_status(self):
        if self._status >= 400:
            raise RuntimeError(f"HTTP {self._status}")


class FakeClient:
    def __init__(self, pages: dict[str, FakeResp]):
        self._pages = pages
        self.requests: list[str] = []

    def get(self, url: str) -> FakeResp:
        self.requests.append(url)
        return self._pages.get(url, FakeResp(status=404))


def _downloader(fake: FakeClient) -> MDFPortalDownloader:
    return MDFPortalDownloader(client=fake)


def test_download_finds_and_validates_class_d(tmp_path):
    search_url = SEARCH_URLS["digikey"].format(part=PART)
    mcd_url = "https://www.digikey.com/static/docs/environmental/MCD_GRM188.xml"
    html = (
        '<html><body>'
        f'<a href="/static/docs/environmental/MCD_GRM188.xml">REACH Material Declaration (IPC-1752)</a>'
        f'<a href="/en/products/detail/{PART}/datasheet">Datasheet PDF</a>'
        '</body></html>'
    )
    fake = FakeClient({
        search_url: FakeResp(html),
        mcd_url: FakeResp(CLASS_D_XML),
    })
    result = _downloader(fake).download(PART, out_dir=str(tmp_path))
    assert result.downloaded is not None
    assert result.downloaded.name == f"{PART}_mdf.xml"
    assert "Barium titanate" in result.downloaded.read_text(encoding="utf-8")
    assert mcd_url in fake.requests


def test_download_no_candidates(tmp_path):
    search_url = SEARCH_URLS["mouser"].format(part=PART)
    fake = FakeClient({search_url: FakeResp("<html><body><a href='/c/'>catalog</a></body></html>")})
    result = _downloader(fake).download(PART, out_dir=str(tmp_path))
    assert result.downloaded is None
    assert result.found == []


def test_download_only_non_xml_candidates_reported(tmp_path):
    search_url = SEARCH_URLS["digikey"].format(part=PART)
    pdf_url = "https://www.digikey.com/docs/rohs-cert.pdf"
    html = '<a href="/docs/rohs-cert.pdf">RoHS certificate PDF</a>'
    fake = FakeClient({search_url: FakeResp(html), pdf_url: FakeResp("PDFBIN")})
    result = _downloader(fake).download(PART, out_dir=str(tmp_path))
    assert result.downloaded is None
    assert pdf_url in result.found
    # i candidati non-XML non vengono scaricati (solo segnalati)
    assert pdf_url not in fake.requests


def test_download_xml_candidate_that_fails_parse(tmp_path):
    search_url = SEARCH_URLS["mouser"].format(part=PART)
    bad_xml_url = "https://www.mouser.com/env/conformity.xml"
    html = f'<a href="/env/conformity.xml">Environmental compliance</a>'
    fake = FakeClient({search_url: FakeResp(html), bad_xml_url: FakeResp("<xml>not ipc</xml>")})
    result = _downloader(fake).download(PART, out_dir=str(tmp_path))
    assert result.downloaded is None
    assert bad_xml_url in result.found


def test_download_unknown_source_reports_error(tmp_path):
    fake = FakeClient({})
    result = _downloader(fake).download(PART, out_dir=str(tmp_path), source="nope")
    assert result.downloaded is None
    assert any("source sconosciuto" in e for e in result.errors)


def test_download_stops_at_first_valid_source(tmp_path):
    # il primo portale (murata) ritorna l'MDF: non deve interrogare digikey
    murata_url = SEARCH_URLS["murata"].format(part=PART)
    mcd_url = "https://www.murata.com/env/MCD.xml"
    html = f'<a href="/env/MCD.xml">Material composition IPC-1752</a>'
    fake = FakeClient({murata_url: FakeResp(html), mcd_url: FakeResp(CLASS_D_XML)})
    result = _downloader(fake).download(PART, out_dir=str(tmp_path))
    assert result.downloaded is not None
    assert fake.requests == [murata_url, mcd_url]