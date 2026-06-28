"""Provider interfaces for external capabilities.

Per RULE.md §5.2 and doc/03-technology-stack.md §10.1, business code must not
bind directly to a specific model, database, or third-party service. External
capabilities are accessed through these interfaces so that concrete
implementations (OpenAI / Qwen / DeepSeek / local models; FAISS / Qdrant /
Milvus; PyMuPDF / Docling / GROBID) remain swappable.

Phase 0 only defines the interface contracts. Concrete implementations are
added in Phase 1.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Abstract LLM provider.

    Implementations wrap a specific vendor SDK (OpenAI-compatible, Qwen,
    DeepSeek, or a local model). Business code depends on this interface, not
    on any concrete SDK.
    """

    def chat(self, messages: list[dict], **kwargs) -> str:
        """Generate a completion from a list of chat messages.

        Args:
            messages: OpenAI-style message list
                (``[{"role": "system", "content": "..."}, ...]``).
            **kwargs: Provider-specific options (temperature, max_tokens, ...).

        Returns:
            The generated text.
        """
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Abstract embedding provider."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: Input strings to embed.

        Returns:
            One embedding vector per input text.
        """
        ...


@runtime_checkable
class RerankerProvider(Protocol):
    """Abstract reranker provider (Phase 2)."""

    def rerank(self, query: str, documents: list[str], top_k: int = 8) -> list[tuple[int, float]]:
        """Re-score documents against a query and return ranked indices.

        Args:
            query: The user query.
            documents: Candidate document texts.
            top_k: Maximum number of results to return.

        Returns:
            List of ``(original_index, score)`` tuples, sorted by score desc.
        """
        ...
