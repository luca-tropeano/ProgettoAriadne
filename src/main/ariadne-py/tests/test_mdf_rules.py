from __future__ import annotations

from ariadne.mdf_rules import (
    classify,
    family_mcd_file,
    normalize_manufacturer,
    reference_url,
)


def test_normalize_manufacturer_aliases():
    assert normalize_manufacturer("Kemet") == "KEMET"
    assert normalize_manufacturer("  ST Microelectronics ") == "STMICROELECTRONICS"
    assert normalize_manufacturer("KEMET OR GENERIC") == "KEMET"
    assert normalize_manufacturer("Yageo") == "YAGEO"


def test_family_mcd_kemet_mlcc():
    assert family_mcd_file("KEMET", "C0603C104K5RACTU") == "MCD-Ceramic.pdf"
    assert family_mcd_file("kemet", "c0805c225k4racauto") == "MCD-Ceramic.pdf"


def test_family_mcd_yageo_mlcc():
    assert family_mcd_file("Yageo", "CC1206KKX7R8BB225") == "MCD-Ceramic.pdf"


def test_family_mcd_kemet_film():
    assert family_mcd_file("KEMET", "C4AKCBUW5100A3SJ") == "mdf_kemet_c4ak_film.pdf"


def test_tdk_mlcc_not_mapped_to_yageo_family():
    # TDK C1608C0G… si era infiltrato nel matching KEMET: non deve succedere
    assert family_mcd_file("TDK", "C1608C0G1H090C080AA") == ""
    info = classify("TDK", "C1608C0G1H090C080AA")
    assert info["status"] == "reference"
    assert reference_url("TDK") == "https://product.tdk.com/en/environment/index.html"


def test_classify_generic_no_mpn():
    info = classify("", "DNF")
    assert info["status"] == "no_mpn"
    assert info["reference_url"] == ""
    assert classify("", "")["status"] == "no_mpn"


def test_classify_rc_hints_yageo():
    info = classify("N.A.", "RC0603JR-070RL")
    assert info["status"] == "reference"
    assert info["manufacturer"] == "YAGEO"
    assert info["reference_url"].startswith("https://yageogroup.com/")

    info2 = classify("N.A.", "PE2512FKE7W0R02L")
    assert info2["manufacturer"] == "YAGEO"


def test_classify_family_mcd_full():
    info = classify("KEMET", "C0603C104M5RACTU")
    assert info["status"] == "family_mcd"
    assert info["mdf_file"] == "MCD-Ceramic.pdf"
    assert "per-serie" in info["note"]