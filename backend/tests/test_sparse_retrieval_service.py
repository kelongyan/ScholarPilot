"""Tests for BM25 sparse retrieval edge cases."""

from __future__ import annotations

from dataclasses import dataclass

from app.services import sparse_retrieval_service


@dataclass
class FakeChunk:
    chunk_id: str
    doc_id: str
    text: str
    section: str = ""
    page_start: int = 1
    page_end: int = 1
    chunk_type: str = "paragraph"
    chunk_index: int = 0


def test_sparse_retrieval_keeps_lexical_matches_with_non_positive_scores(
    monkeypatch,
) -> None:
    chunks = [
        FakeChunk(
            chunk_id="chunk-1",
            doc_id="doc-1",
            text="The method uses a cross encoder reranker.",
            chunk_index=0,
        ),
        FakeChunk(
            chunk_id="chunk-2",
            doc_id="doc-1",
            text="This paragraph is unrelated.",
            chunk_index=1,
        ),
        FakeChunk(
            chunk_id="chunk-3",
            doc_id="doc-1",
            text="Experiments report 92.3 percent accuracy.",
            chunk_index=2,
        ),
    ]

    class FakeBM25:
        def __init__(self, corpus: list[list[str]]) -> None:
            self.corpus = corpus

        def get_scores(self, query_terms: list[str]) -> list[float]:
            return [-0.2, -0.4, 0.0]

    monkeypatch.setattr(
        sparse_retrieval_service.document_repo,
        "list_chunks",
        lambda db, doc_id: chunks,
    )
    monkeypatch.setattr(sparse_retrieval_service, "BM25Okapi", FakeBM25)

    hits = sparse_retrieval_service.retrieve_sparse(
        object(),
        "What reranker and accuracy are reported?",
        doc_id="doc-1",
        top_k=8,
    )

    assert [hit.chunk_id for hit in hits] == ["chunk-3", "chunk-1"]
    assert all(hit.score >= 0 for hit in hits)


def test_sparse_retrieval_ignores_stopword_only_query(monkeypatch) -> None:
    monkeypatch.setattr(
        sparse_retrieval_service.document_repo,
        "list_chunks",
        lambda db, doc_id: [
            FakeChunk(chunk_id="chunk-1", doc_id="doc-1", text="Any content.")
        ],
    )

    hits = sparse_retrieval_service.retrieve_sparse(
        object(),
        "what is the and",
        doc_id="doc-1",
        top_k=8,
    )

    assert hits == []
