"""Sparse retrieval service for Phase 2 hybrid RAG.

Uses BM25 over indexed chunk text stored in PostgreSQL rows. The service
boundary stays separate from dense retrieval so this implementation can later
be replaced by another sparse engine without changing orchestration.
"""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.repositories import document_repo
from app.services.vector_service import RetrievedChunk

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "what",
    "which",
    "with",
}


def retrieve_sparse(
    db: Session,
    query: str,
    *,
    doc_id: str,
    top_k: int,
) -> list[RetrievedChunk]:
    """Retrieve chunks by BM25 within a single document."""
    chunks = document_repo.list_chunks(db, doc_id)
    if not chunks:
        return []

    tokenized_corpus = [_tokenize(chunk.text) for chunk in chunks]
    query_terms = _tokenize(query)
    if not query_terms:
        return []

    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(query_terms)

    matching: list[tuple[float, object]] = []
    for score, chunk, terms in zip(scores, chunks, tokenized_corpus, strict=True):
        if not set(query_terms).isdisjoint(terms):
            matching.append((float(score), chunk))

    if not matching:
        return []

    min_score = min(score for score, _ in matching)
    shift = -min_score if min_score < 0 else 0.0
    ranked = sorted(
        ((score + shift, score, chunk) for score, chunk in matching),
        key=lambda item: item[1],
        reverse=True,
    )[:top_k]

    return [
        RetrievedChunk(
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            text=chunk.text,
            section=chunk.section,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            chunk_type=chunk.chunk_type,
            chunk_index=chunk.chunk_index,
            score=normalized_score,
        )
        for normalized_score, _raw_score, chunk in ranked
    ]


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in (match.lower() for match in _TOKEN_RE.findall(text))
        if token not in _STOPWORDS
    ]
