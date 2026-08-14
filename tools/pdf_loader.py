"""Extract text from an uploaded PDF."""

from __future__ import annotations

import io

from pypdf import PdfReader


def extract_pdf_text(file_bytes: bytes, max_chars: int = 20_000) -> str:
    """Return concatenated page text from a PDF, truncated to max_chars. Raises on failure."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()
    return text[:max_chars]
