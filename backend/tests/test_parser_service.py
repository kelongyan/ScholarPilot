"""Tests for the PDF parser service."""

from __future__ import annotations

from pathlib import Path

from app.services.parser_service import parse_pdf
from tests.conftest import make_test_pdf


def test_parse_pdf_extracts_pages(tmp_path: Path) -> None:
    """parse_pdf returns one ParsedPage per page with 1-based numbers."""
    pdf_path = make_test_pdf(
        tmp_path / "sample.pdf",
        ["Introduction to RAG.", "Methods and experiments."],
    )

    parsed = parse_pdf(str(pdf_path))

    assert parsed.page_count == 2
    assert len(parsed.pages) == 2
    assert parsed.pages[0].page == 1
    assert parsed.pages[1].page == 2
    assert "Introduction" in parsed.pages[0].text
    assert "Methods" in parsed.pages[1].text


def test_parse_pdf_single_page(tmp_path: Path) -> None:
    """parse_pdf handles a single-page document."""
    pdf_path = make_test_pdf(tmp_path / "one.pdf", ["Only page."])

    parsed = parse_pdf(str(pdf_path))

    assert parsed.page_count == 1
    assert parsed.pages[0].page == 1
    assert "Only page" in parsed.pages[0].text
