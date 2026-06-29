"""Citation service.

Builds citation objects from retrieved chunks so answers stay traceable to
their source (doc_id, chunk_id, page, original text, score). Per RULE.md §6.1,
every RAG answer must carry this evidence chain.
"""

from __future__ import annotations

from app.models import Citation
from app.services.vector_service import RetrievedChunk


def build_citations(
    retrieved: list[RetrievedChunk],
    *,
    quote_max_chars: int = 400,
) -> list[Citation]:
    """Build :class:`Citation` ORM objects from retrieved chunks.

    Args:
        retrieved: Chunks returned by the vector store.
        quote_max_chars: Maximum length of the quoted original text.

    Returns:
        Unsaved Citation objects (caller persists them).
    """
    citations: list[Citation] = []
    for chunk in retrieved:
        quote = chunk.text[:quote_max_chars]
        citations.append(
            Citation(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                quote=quote,
                page=chunk.page_start,
                score=chunk.score,
            )
        )
    return citations
