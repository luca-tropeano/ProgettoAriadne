from __future__ import annotations

from pathlib import Path

import pytest

from ariadne.pdf_extractor import extract_text_from_pdf, extract_text_from_pdf_stream

TEST_DATA = Path(__file__).parent.parent / "test_data"


def test_extract_real_pdf():
    pdf = TEST_DATA / "stm_bom.pdf"
    if not pdf.exists():
        pytest.skip("stm_bom.pdf not present (gitignored)")
    text = extract_text_from_pdf(str(pdf))
    assert "--- Page 1 ---" in text
    assert len(text.strip()) > 0


def test_extract_stream_matches_file():
    pdf = TEST_DATA / "stm_bom.pdf"
    if not pdf.exists():
        pytest.skip("stm_bom.pdf not present (gitignored)")
    with open(pdf, "rb") as f:
        stream_text = extract_text_from_pdf_stream(f)
    file_text = extract_text_from_pdf(str(pdf))
    assert stream_text == file_text


def test_extract_missing_file_raises():
    with pytest.raises(Exception):
        extract_text_from_pdf(str(TEST_DATA / "does_not_exist.pdf"))


def test_extract_invalid_pdf_raises(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a real pdf")
    with pytest.raises(Exception):
        extract_text_from_pdf(str(bad))