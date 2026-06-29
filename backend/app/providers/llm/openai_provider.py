"""OpenAI-compatible LLM provider.

Covers OpenAI itself and any endpoint that speaks the OpenAI Chat Completions
protocol (Qwen, DeepSeek, local vLLM/Ollama via ``base_url`` override).
"""

from __future__ import annotations

from openai import OpenAI

from app.core.config import get_settings


class OpenAILLMProvider:
    """LLM provider backed by the OpenAI Python SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.llm_model
        self._client = OpenAI(
            api_key=api_key or settings.llm_api_key or "not-set",
            base_url=base_url or settings.llm_base_url,
        )

    def chat(self, messages: list[dict], **kwargs) -> str:
        """Generate a completion via the OpenAI Chat Completions API."""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content or ""
