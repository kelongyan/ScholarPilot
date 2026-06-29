"""LLM provider factory.

Selects a concrete :class:`~app.providers.base.LLMProvider` based on
``settings.llm_provider``. Supported values:

- ``openai``    — OpenAI and any OpenAI-compatible endpoint (Qwen, DeepSeek,
                  local vLLM/Ollama via ``llm_base_url``).
- ``anthropic`` — Anthropic Claude.
- ``local``     — local model exposed via an OpenAI-compatible endpoint
                  (e.g. Ollama's ``/v1``); falls back to the OpenAI adapter.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.providers.base import LLMProvider
from app.providers.llm.anthropic_provider import AnthropicLLMProvider
from app.providers.llm.openai_provider import OpenAILLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider instance (cached)."""
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        return AnthropicLLMProvider()
    if provider in {"openai", "local"}:
        # "local" reuses the OpenAI-compatible adapter pointed at a local
        # endpoint (e.g. Ollama) via llm_base_url.
        return OpenAILLMProvider()
    msg = f"Unknown llm_provider: {provider!r}. Use openai | anthropic | local."
    raise ValueError(msg)
