import tempfile
from pathlib import Path

from ariadne.excel_parser import _detect_mounting_type


def test_detect_mounting_type_smt():
    assert _detect_mounting_type("0603") == "SMT"
    assert _detect_mounting_type("SOT23") == "SMT"
    assert _detect_mounting_type("LQFP48") == "SMT"


def test_detect_mounting_type_tht():
    assert _detect_mounting_type("DIP-8") == "THT"
    assert _detect_mounting_type("SIP-3") == "THT"
    assert _detect_mounting_type("TO-220") == "THT"


def test_detect_mounting_type_unknown():
    assert _detect_mounting_type(None) == "SMT"
    assert _detect_mounting_type("") == "SMT"
    assert _detect_mounting_type("  ") == "SMT"
