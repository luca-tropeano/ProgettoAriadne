from __future__ import annotations

from ariadne.lzstring import decompress, decompress_from_base64


def test_decompress_base64_known_vector():
    # Reference vectors from lz-string@1.5.0.
    assert decompress_from_base64("BIUwNmD2A0AEDqkBOYAmBCIA") == "Hello, World!"


def test_decompress_base64_utf8():
    # Compressed from the reference implementation. Decodes to "hello, i am a \u732b".
    out = decompress_from_base64("BYUwNmD2A0AECWsCGBbZtDUzkA==")
    assert out == "hello, i am a \u732b"


def test_decompress_base64_none_empty():
    assert decompress_from_base64(None) == ""
    assert decompress_from_base64("") is None


def test_decompress_invalid_suffix():
    out = decompress_from_base64(
        "N4IgtgpgLghgJjWIBcACUUCWUA2EWogAqEAzlCADSEBOEAbpqZgPYB2BI"
    )
    # Decompression should not raise even on truncated input.
    assert out is None or isinstance(out, str)


def test_decompress_plain_roundtrip_subset():
    assert decompress(None) == ""
    assert decompress("") is None
