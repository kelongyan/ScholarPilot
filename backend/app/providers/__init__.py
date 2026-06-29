"""Provider interfaces and factories for external capabilities.

Business code depends on :class:`~app.providers.base.LLMProvider` and
:class:`~app.providers.base.EmbeddingProvider`, never on a concrete SDK.
Use :func:`get_llm_provider` and :func:`get_embedding_provider` to obtain an
instance selected by application settings.
"""

from __future__ import annotations

from app.providers.base import EmbeddingProvider, LLMProvider, RerankerProvider
from app.providers.embedding.factory import get_embedding_provider
from app.providers.llm.factory import get_llm_provider

__all__ = [
    "EmbeddingProvider",
    "LLMProvider",
    "RerankerProvider",
    "get_embedding_provider",
    "get_llm_provider",
]
