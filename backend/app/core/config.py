"""Application configuration.

Settings are loaded from environment variables (or a local ``.env`` file).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    All values can be overridden via environment variables. Copy
    ``.env.example`` to ``.env`` and adjust as needed.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Kairos"
    app_version: str = "0.1.0"
    api_prefix: str = ""
    debug: bool = False

    # --- Storage ---
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/kairos"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "chunks"
    # Local filesystem path for uploaded PDFs and parsed artifacts.
    storage_dir: str = "storage"

    # --- LLM provider ---
    # Provider can be: openai | anthropic | local
    # "openai" covers OpenAI and any OpenAI-compatible endpoint
    # (Qwen, DeepSeek, local vLLM/Ollama via base_url override).
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    # --- Embedding provider ---
    # Provider can be: openai | local
    embedding_provider: str = "openai"
    embedding_api_key: str = ""
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # --- RAG ---
    retrieval_top_k: int = 5
    sparse_retrieval_top_k: int = 8
    rerank_top_k: int = 5
    reranker_provider: str = "simple"
    chunk_size: int = 800
    chunk_overlap: int = 120

    # --- Async (RQ) ---
    rq_queue_name: str = "default"

    # --- Auth / RBAC ---
    # Disabled by default so local development and existing tests keep working
    # until explicit tokens or JWT are configured.
    auth_enabled: bool = False
    auth_jwt_secret: str = ""
    auth_admin_token: str = ""
    auth_kb_manager_token: str = ""
    auth_user_token: str = ""
    auth_dev_actor_id: str = "system"


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
