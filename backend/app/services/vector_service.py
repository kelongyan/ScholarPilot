"""Vector store service (Qdrant).

Indexes chunk embeddings and retrieves the top-k most similar chunks for a
query, optionally filtered by ``doc_id`` for single-paper Q&A.
"""

from __future__ import annotations

from dataclasses import dataclass

from qdrant_client.http import models as qdrant_models

from app.core.config import get_settings
from app.core.qdrant import ensure_collection, qdrant_client


@dataclass
class RetrievedChunk:
    """A retrieved chunk with its provenance and similarity score."""

    chunk_id: str
    doc_id: str
    text: str
    section: str
    page_start: int
    page_end: int
    chunk_type: str
    chunk_index: int
    score: float


def index_chunks(
    doc_id: str,
    chunks: list[dict],
    vectors: list[list[float]],
) -> None:
    """Upsert chunk embeddings into Qdrant.

    Args:
        doc_id: The document id (stored as payload for filtering).
        chunks: Chunk metadata dicts (must include ``chunk_id`` and provenance).
        vectors: Embedding vectors, one per chunk, aligned with ``chunks``.
    """
    ensure_collection()
    settings = get_settings()
    points = [
        qdrant_models.PointStruct(
            id=chunk["chunk_id"],
            vector=vector,
            payload={
                "doc_id": doc_id,
                "chunk_id": chunk["chunk_id"],
                "section": chunk.get("section", ""),
                "page_start": chunk.get("page_start", 0),
                "page_end": chunk.get("page_end", 0),
                "chunk_type": chunk.get("chunk_type", "paragraph"),
                "chunk_index": chunk.get("chunk_index", 0),
                "text": chunk.get("text", ""),
            },
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    qdrant_client.upsert(collection_name=settings.qdrant_collection, points=points)


def retrieve(
    query_vector: list[float],
    *,
    doc_id: str | None = None,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Retrieve the top-k most similar chunks for a query vector.

    Args:
        query_vector: The embedded query.
        doc_id: If given, restrict retrieval to a single document.
        top_k: Number of results (defaults to settings.retrieval_top_k).

    Returns:
        A list of :class:`RetrievedChunk` sorted by similarity desc.
    """
    ensure_collection()
    settings = get_settings()
    k = top_k or settings.retrieval_top_k

    query_filter = None
    if doc_id:
        query_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="doc_id",
                    match=qdrant_models.MatchValue(value=doc_id),
                )
            ]
        )

    results = qdrant_client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=k,
        query_filter=query_filter,
        with_payload=True,
    )
    return [
        RetrievedChunk(
            chunk_id=hit.payload.get("chunk_id", ""),
            doc_id=hit.payload.get("doc_id", ""),
            text=hit.payload.get("text", ""),
            section=hit.payload.get("section", ""),
            page_start=hit.payload.get("page_start", 0),
            page_end=hit.payload.get("page_end", 0),
            chunk_type=hit.payload.get("chunk_type", "paragraph"),
            chunk_index=hit.payload.get("chunk_index", 0),
            score=hit.score,
        )
        for hit in results
    ]


def delete_document_vectors(doc_id: str) -> None:
    """Remove all vectors for a document (used on reindex)."""
    settings = get_settings()
    qdrant_client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=qdrant_models.FilterSelector(
            filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="doc_id",
                        match=qdrant_models.MatchValue(value=doc_id),
                    )
                ]
            )
        ),
    )
