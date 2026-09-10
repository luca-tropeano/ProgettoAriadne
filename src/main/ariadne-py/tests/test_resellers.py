from __future__ import annotations

from ariadne.resellers import reseller_links


def test_reseller_links_empty_without_mpn():
    assert reseller_links(None) == []
    assert reseller_links("   ") == []


def test_reseller_links_generates_all_distributors():
    links = reseller_links("RC0603FR-0710KL")
    assert len(links) >= 5
    urls = {l["name"]: l["url"] for l in links}
    assert "digikey.it" in urls["DigiKey"]
    assert "mouser.it" in urls["Mouser"]
    assert "farnell.com" in urls["Farnell"]
    assert "rs-online.com" in urls["RS"]
    assert "octopart.com" in urls["Octopart"]


def test_reseller_links_url_encodes_mpn():
    links = reseller_links("ABC /123")
    url = links[0]["url"]
    assert "%20" in url or "%2F" in url
    assert "ABC" in url