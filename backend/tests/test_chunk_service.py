"""Tests for the chunking service."""

from __future__ import annotations

from app.services.chunk_service import chunk_document
from app.services.parser_service import ParsedDocument, ParsedPage


def test_chunk_document_preserves_page_provenance() -> None:
    """Chunks carry their source page range and a sequential index."""
    parsed = ParsedDocument(
        page_count=2,
        pages=[
            ParsedPage(page=1, text="First paragraph.\n\nSecond paragraph."),
            ParsedPage(page=2, text="Third paragraph on page two."),
        ],
    )

    chunks = chunk_document(parsed, doc_id="doc-1", chunk_size=10000)

    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.page_start >= 1
        assert chunk.page_end >= chunk.page_start
        assert chunk.chunk_index >= 0
        assert chunk.token_count > 0
        assert chunk.text  # non-empty


def test_chunk_document_empty_pages_returns_empty() -> None:
    """Empty pages produce no chunks."""
    parsed = ParsedDocument(page_count=1, pages=[ParsedPage(page=1, text="")])

    chunks = chunk_document(parsed, doc_id="doc-1")

    assert chunks == []


def test_chunk_document_splits_large_content() -> None:
    """Content exceeding chunk_size is split into multiple chunks."""
    # Many paragraphs to force a split with a small chunk_size.
    paragraphs = [f"Paragraph number {i} with some words." for i in range(50)]
    parsed = ParsedDocument(
        page_count=1,
        pages=[ParsedPage(page=1, text="\n\n".join(paragraphs))],
    )

    chunks = chunk_document(parsed, doc_id="doc-1", chunk_size=50, chunk_overlap=10)

    assert len(chunks) > 1
    # Indices are sequential starting at 0.
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
