"""Test fixtures and helpers.

Generates a small in-memory PDF so parser tests don't depend on a binary
fixture file checked into the repo.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def make_test_pdf(path: Path, pages: list[str]) -> Path:
    """Create a small PDF with the given page texts.

    Args:
        path: Where to write the PDF.
        pages: One string per page.

    Returns:
        The path to the written PDF.
    """
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()
    return path
