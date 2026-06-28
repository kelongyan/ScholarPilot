"""Application configuration.

Settings are loaded from environment variables (or a local ``.env`` file).
Phase 0 only establishes the configuration structure; the storage and model
services are not connected until Phase 1.
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
    app_name: str = "ScholarPilot"
    app_version: str = "0.1.0"
    api_prefix: str = ""
    debug: bool = False

    # --- Storage (Phase 1 dependencies, reserved here) ---
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/scholarpilot"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    # --- LLM provider (cloud + local reserved) ---
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    # --- Embedding provider (cloud + local reserved) ---
    embedding_provider: str = "openai"
    embedding_api_key: str = ""
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
