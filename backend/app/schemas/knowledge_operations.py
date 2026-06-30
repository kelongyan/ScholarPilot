"""Schemas for knowledge operations suggestions."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeOperationSuggestionResponse(BaseModel):
    """A deterministic draft suggestion for improving a knowledge base."""

    suggestion_id: str
    knowledge_base_id: str | None = None
    doc_id: str | None = None
    question_log_id: str | None = None
    suggestion_type: str
    severity: str
    title: str
    description: str
    suggested_action: str
    status: str = "pending"
    evidence: list[dict[str, object]] = Field(default_factory=list)
    created_at: datetime | None = None


class KnowledgeOperationSuggestionListResponse(BaseModel):
    """List of knowledge operation suggestions."""

    suggestions: list[KnowledgeOperationSuggestionResponse]
