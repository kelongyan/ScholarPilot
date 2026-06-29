"""Tests for the citation service."""

from __future__ import annotations

from app.services.citation_service import build_citations
from app.services.vector_service import RetrievedChunk


def test_build_citations_carries_provenance() -> None:
    """Citations carry doc_id, chunk_id, page, quote, and score."""
    retrieved = [
        RetrievedChunk(
            chunk_id="chunk-1",
            doc_id="doc-1",
            text="Some evidence text here.",
            section="Method",
            page_start=3,
            page_end=4,
            chunk_type="paragraph",
            chunk_index=0,
            score=0.92,
        )
    ]

    citations = build_citations(retrieved)

    assert len(citations) == 1
    c = citations[0]
    assert c.chunk_id == "chunk-1"
    assert c.doc_id == "doc-1"
    assert c.page == 3
    assert c.score == 0.92
    assert "Some evidence" in c.quote


def test_build_citations_truncates_long_quotes() -> None:
    """Quotes longer than the limit are truncated."""
    long_text = "x" * 1000
    retrieved = [
        RetrievedChunk(
            chunk_id="chunk-1",
            doc_id="doc-1",
            text=long_text,
            section="",
            page_start=1,
            page_end=1,
            chunk_type="paragraph",
            chunk_index=0,
            score=0.5,
        )
    ]

    citations = build_citations(retrieved, quote_max_chars=100)

    assert len(citations[0].quote) == 100


def test_build_citations_empty_input() -> None:
    """No retrieved chunks yields no citations."""
    assert build_citations([]) == []
