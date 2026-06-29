"""Embedding provider factory.

Selects a concrete :class:`~app.providers.base.EmbeddingProvider` based on
``settings.embedding_provider``. Supported values:

- ``openai`` — OpenAI and any OpenAI-compatible embedding endpoint.
- ``local``  — local sentence-transformers model (BGE-M3, E5, ...).
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.providers.base import EmbeddingProvider
from app.providers.embedding.openai_provider import OpenAIEmbeddingProvider


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider instance (cached)."""
    settings = get_settings()
    provider = settings.embedding_provider.lower()

    if provider == "local":
        from app.providers.embedding.local_provider import LocalEmbeddingProvider

        return LocalEmbeddingProvider()
    if provider == "openai":
        return OpenAIEmbeddingProvider()
    msg = f"Unknown embedding_provider: {provider!r}. Use openai | local."
    raise ValueError(msg)
