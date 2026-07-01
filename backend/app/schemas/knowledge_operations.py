"""Schemas for knowledge operations suggestions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

KnowledgeOperationStatus = Literal[
    "pending",
    "resolved",
    "ignored",
    "reindexed",
    "document_added",
]


class KnowledgeOperationItemResponse(BaseModel):
    """A persisted actionable item for improving a knowledge base."""

    model_config = ConfigDict(from_attributes=True)

    item_id: str
    knowledge_base_id: str | None = None
    doc_id: str | None = None
    question_log_id: str | None = None
    agent_run_id: str | None = None
    source_type: str
    source_id: str
    suggestion_type: str
    aggregate_key: str = ""
    signal_count: int = 1
    last_signal_at: datetime | None = None
    severity: str
    title: str
    description: str
    suggested_action: str
    status: str
    resolution_note: str = ""
    created_at: datetime
    updated_at: datetime


class KnowledgeOperationItemUpdateRequest(BaseModel):
    """Update payload for handling a knowledge operation item."""

    status: KnowledgeOperationStatus
    resolution_note: str = Field(default="", max_length=2000)


class KnowledgeOperationItemListResponse(BaseModel):
    """List of persisted knowledge operation items."""

    items: list[KnowledgeOperationItemResponse]


class KnowledgeOperationEventResponse(BaseModel):
    """A structured lifecycle event for a knowledge operation item."""

    model_config = ConfigDict(from_attributes=True)

    event_id: str
    item_id: str
    knowledge_base_id: str | None = None
    event_type: str
    actor_id: str
    source_type: str
    source_id: str
    suggestion_type: str
    status: str
    note: str = ""
    detail_json: dict[str, object] = Field(default_factory=dict)
    created_at: datetime


class KnowledgeOperationEventListResponse(BaseModel):
    """List of structured lifecycle events for an operation item."""

    events: list[KnowledgeOperationEventResponse]


class KnowledgeOperationDraftResponse(BaseModel):
    """A draft FAQ or source-material note created from an operation item."""

    model_config = ConfigDict(from_attributes=True)

    draft_id: str
    item_id: str
    knowledge_base_id: str | None = None
    doc_id: str | None = None
    question_log_id: str | None = None
    draft_type: str
    status: str
    title: str
    question: str
    answer: str
    source_note: str
    created_by: str
    created_at: datetime
    updated_at: datetime


class KnowledgeOperationDraftListResponse(BaseModel):
    """List of draft knowledge assets created from operation handling."""

    drafts: list[KnowledgeOperationDraftResponse]


class KnowledgeOperationSuggestionResponse(BaseModel):
    """Backward-compatible generated suggestion representation."""

    model_config = ConfigDict(from_attributes=True)

    suggestion_id: str
    item_id: str
    knowledge_base_id: str | None = None
    doc_id: str | None = None
    question_log_id: str | None = None
    agent_run_id: str | None = None
    source_type: str
    source_id: str
    suggestion_type: str
    aggregate_key: str = ""
    signal_count: int = 1
    last_signal_at: datetime | None = None
    severity: str
    title: str
    description: str
    suggested_action: str
    status: str
    resolution_note: str = ""
    evidence: list[dict[str, object]] = Field(default_factory=list)
    created_at: datetime | None = None


class KnowledgeOperationSuggestionListResponse(BaseModel):
    """Backward-compatible list of knowledge operation suggestions."""

    suggestions: list[KnowledgeOperationSuggestionResponse]
