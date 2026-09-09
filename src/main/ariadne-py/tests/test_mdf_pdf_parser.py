from __future__ import annotations

import pytest

from ariadne.mdf_pdf_parser import parse_mdf_tables


def _zvei_tables():
    return [
        # tabella metadata 1 (familia / identifier)
        [["Product", "Product name/family name", "Electronic component / 47xx",
          "Content of the declaration", "Composition declaration"],
         ["", "Identifier", "4711", "Version IEC Database", "n.A."],
         ["", "Package", "TO263", "", ""]],
        # tabella metadata 2 (Mass / Unit)
        [["Company", "Company", "Name, Identifier", "Date / Version", "06.03.2018 / 1.0"],
         ["", "Contact", "Name, E-Mail of contact person", "Mass", "6,3"],
         ["", "Authorizer", "Name, E-Mail", "Unit", "mg"]],
        # tabella sostanze: header a 12 colonne (ZVEI), massa in mg e CAS dopo la sostanza
        [["Item / SubItem Name", "ProductPart", "Weight [mg]", "Material name",
          "Classi- fication", "Weight [mg]", "Mass Percent", "Substance Name", "CAS #",
          "Exemptions", "Weight [mg]", "Mass Percent"],
         ["MLCC 47 nF", "Active part", "4,35", "ceramics", "7.2", "4,35", "69",
          "ceramic without declarable substances", "pseudo substance", "-", "1,96", "45"],
         ["", "Inner electrode", "0,68", "nickel", "3.4", "0,68", "10,8",
          "nickel", "7440-02-0", "-", "3,4", "100"],
         ["", "Inner electrode", "", "", "", "", "",
          "nickel", "7440-02-0", "-", "0,049", "99,95"],  # riga duplicata → merge
         ["", "", "", "", "", "", "", "barium", "7440-39-3", "-", "2,4", "55"],
         ["", "Termination", "1,27", "Sn", "4.2", "0,12", "1,9",
          "tin", "7440-31-5", "-", "0,119", "99,9 - 100"]],
    ]


def _kemet_tables():
    return [
        [["Pitch mm", "", "", "", "27.5", "37.5"],
         ["HomogeneousLevel", "Material", "Substance", "CAS No.", "MAXIMUM size", "MAXIMUM size"],
         ["", "", "", "", "Weight (gr)", "Weight (gr)"],
         ["Element", "Thermoplastics", "PP", "9003-07-0", "69,94", "84,639"],
         ["Element", "Substance", "Sn", "7440-31-5", "5,327", "-"],
         ["", "", "misc.", "system", "-", "-"],
         ["Aggregate", "Substance", "Halogenated Flame Ret.", "Multi", "-", "-"]],
    ]


def test_parse_mdf_tables_zvei_layout():
    mdf = parse_mdf_tables(_zvei_tables())
    assert mdf.component_name == "MLCC 47 nF"
    assert mdf.total_mass_mg == pytest.approx(6.3)
    assert mdf.part_numbers == []
    by_cas = {s.cas: s for s in mdf.substances}
    # la riga con CAS 'pseudo substance' è stata scartata
    assert "pseudo substance" not in by_cas
    # nickel duplicato → sommato (3,4 + 0,049)
    assert by_cas["7440-02-0"].mass_mg == pytest.approx(3.449)
    assert by_cas["7440-02-0"].concentration_pct == pytest.approx(100.0)
    assert by_cas["7440-39-3"].mass_mg == pytest.approx(2.4)
    assert by_cas["7440-39-3"].concentration_pct == pytest.approx(55.0)
    # intervallo '99,9 - 100' → estremo massimo
    tin = by_cas["7440-31-5"]
    assert tin.mass_mg == pytest.approx(0.119)
    assert tin.concentration_pct == pytest.approx(100.0)


def test_parse_mdf_tables_kemet_gr_to_mg():
    mdf = parse_mdf_tables(_kemet_tables())
    assert mdf.total_mass_mg is None
    assert len(mdf.substances) == 2
    pp = next(s for s in mdf.substances if s.cas == "9003-07-0")
    # 'Weight (gr)' a destra del CAS → conversione 69,94 gr = 69940 mg
    assert pp.mass_mg == pytest.approx(69940.0)
    sn = next(s for s in mdf.substances if s.cas == "7440-31-5")
    assert sn.mass_mg == pytest.approx(5327.0)
    # placeholder 'system'/'Multi' → warning per 'Multi' (non-placeholder), nessuna sostanza
    assert any("Multi" in w for w in mdf.warnings)
    assert not any("system" in w.lower() for w in mdf.warnings)
    assert all(s.cas in ("9003-07-0", "7440-31-5") for s in mdf.substances)


def test_parse_mdf_tables_part_numbers_from_text():
    text = "Murata GRM188R61E225MA12D MLCC reflow not-for-wave"
    mdf = parse_mdf_tables(_zvei_tables(), all_text=text)
    assert "GRM188R61E225MA12D" in mdf.part_numbers