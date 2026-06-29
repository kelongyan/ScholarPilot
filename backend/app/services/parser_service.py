"""PDF parsing service.

Uses PyMuPDF to extract text with page numbers. Phase 1 keeps parsing simple:
plain text per page plus a best-effort section title. Layout-aware parsing
(tables, figures, formulas) is deferred to Phase 4 (Docling).
"""

from __future__ import annotations

from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass
class ParsedPage:
    """A single parsed page: its 1-based page number and extracted text."""

    page: int
    text: str


@dataclass
class ParsedDocument:
    """Result of parsing a PDF: page count and per-page text."""

    page_count: int
    pages: list[ParsedPage]


def parse_pdf(file_path: str) -> ParsedDocument:
    """Parse a PDF file into per-page text.

    Args:
        file_path: Path to the PDF on disk.

    Returns:
        A :class:`ParsedDocument` with one :class:`ParsedPage` per page
        (1-based page numbers).
    """
    doc = fitz.open(file_path)
    pages: list[ParsedPage] = []
    for index, page in enumerate(doc):
        # 1-based page number to match how readers display pages.
        pages.append(ParsedPage(page=index + 1, text=page.get_text("text")))
    page_count = doc.page_count
    doc.close()
    return ParsedDocument(page_count=page_count, pages=pages)
