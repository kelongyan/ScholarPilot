"""Qdrant vector store client."""

from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.core.config import get_settings

settings = get_settings()

qdrant_client = QdrantClient(url=settings.qdrant_url)


def ensure_collection() -> None:
    """Create the chunks collection if it does not exist.

    Called at app startup and from the worker. Safe to call repeatedly.
    """
    collections = qdrant_client.get_collections().collections
    names = {c.name for c in collections}
    if settings.qdrant_collection not in names:
        qdrant_client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=qdrant_models.VectorParams(
                size=settings.embedding_dim,
                distance=qdrant_models.Distance.COSINE,
            ),
        )
