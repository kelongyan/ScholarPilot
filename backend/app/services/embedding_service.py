"""Embedding service.

Thin wrapper around the configured :class:`EmbeddingProvider`. Batches
requests to stay within provider limits.
"""

from __future__ import annotations

from app.providers import get_embedding_provider


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts.

    Args:
        texts: Input strings.

    Returns:
        One embedding vector per input text, in order.
    """
    if not texts:
        return []
    provider = get_embedding_provider()
    # Batch in groups of 64 to respect typical embedding API limits.
    batch_size = 64
    results: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        results.extend(provider.embed(batch))
    return results


def embed_query(query: str) -> list[float]:
    """Generate an embedding for a single query string."""
    vectors = embed_texts([query])
    return vectors[0] if vectors else []
