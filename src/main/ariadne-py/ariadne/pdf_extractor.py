from __future__ import annotations

import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"--- Page {i + 1} ---\n{text}")
    return "\n\n".join(pages)


def extract_text_from_pdf_stream(stream) -> str:
    pages = []
    with pdfplumber.open(stream) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"--- Page {i + 1} ---\n{text}")
    return "\n\n".join(pages)
