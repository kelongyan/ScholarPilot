"""Local embedding provider via sentence-transformers.

Optional dependency (install with ``uv sync --extra local``). Useful for
offline / cost-sensitive setups with models like BGE-M3 or E5.
"""

from __future__ import annotations

from app.core.config import get_settings


class LocalEmbeddingProvider:
    """Embedding provider backed by a local sentence-transformers model."""

    def __init__(self, model_name: str | None = None) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:  # pragma: no cover
            msg = (
                "sentence-transformers is not installed. "
                "Install with: uv sync --extra local"
            )
            raise ImportError(msg) from e

        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self._model = SentenceTransformer(self.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if not texts:
            return []
        vectors = self._model.encode(texts, convert_to_numpy=True)
        return [v.tolist() for v in vectors]
