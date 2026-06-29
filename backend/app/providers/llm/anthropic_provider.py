"""Anthropic Claude LLM provider."""

from __future__ import annotations

from anthropic import Anthropic

from app.core.config import get_settings


class AnthropicLLMProvider:
    """LLM provider backed by the Anthropic Python SDK (Claude)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.llm_model
        self._client = Anthropic(api_key=api_key or settings.llm_api_key)

    def chat(self, messages: list[dict], **kwargs) -> str:
        """Generate a completion via the Anthropic Messages API.

        Anthropic separates the system prompt from the conversation, so the
        OpenAI-style ``messages`` list is adapted: any ``system`` message is
        extracted and passed as ``system``.
        """
        system_parts: list[str] = []
        convo: list[dict] = []
        for msg in messages:
            if msg.get("role") == "system":
                system_parts.append(msg.get("content", ""))
            else:
                convo.append(msg)

        # Pop provider-specific kwargs that Anthropic handles differently.
        max_tokens = kwargs.pop("max_tokens", 1024)
        temperature = kwargs.pop("temperature", None)

        response = self._client.messages.create(
            model=self.model,
            system="\n\n".join(system_parts) if system_parts else None,
            messages=convo,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )
        return response.content[0].text if response.content else ""
