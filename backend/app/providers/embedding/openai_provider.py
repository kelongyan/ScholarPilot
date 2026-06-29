"""OpenAI-compatible embedding provider.

Covers OpenAI text-embedding models and any OpenAI-compatible embedding
endpoint (Qwen, DeepSeek, local services via ``embedding_base_url``).
"""

from __future__ import annotations

from openai import OpenAI

from app.core.config import get_settings


class OpenAIEmbeddingProvider:
    """Embedding provider backed by the OpenAI Python SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.embedding_model
        self._client = OpenAI(
            api_key=api_key or settings.embedding_api_key or "not-set",
            base_url=base_url or settings.embedding_base_url,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if not texts:
            return []
        response = self._client.embeddings.create(model=self.model, input=texts)
        # Sort by index to guarantee input order is preserved.
        sorted_data = sorted(response.data, key=lambda d: d.index)
        return [d.embedding for d in sorted_data]
