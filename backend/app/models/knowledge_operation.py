"""Knowledge operation item ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class KnowledgeOperationItem(Base):
    """A persisted actionable item for knowledge-base quality operations."""

    __tablename__ = "knowledge_operation_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    knowledge_base_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("knowledge_bases.knowledge_base_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    doc_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("documents.doc_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    question_log_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("question_logs.question_log_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_run_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("agent_runs.run_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    source_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    suggestion_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    aggregate_key: Mapped[str] = mapped_column(String(256), default="", index=True)
    signal_count: Mapped[int] = mapped_column(Integer, default=1)
    last_signal_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    severity: Mapped[str] = mapped_column(String(32), default="medium", index=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    suggested_action: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    resolution_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class KnowledgeOperationEvent(Base):
    """A structured event in a knowledge operation item's lifecycle."""

    __tablename__ = "knowledge_operation_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("knowledge_operation_items.item_id", ondelete="CASCADE"),
        index=True,
    )
    knowledge_base_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("knowledge_bases.knowledge_base_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    actor_id: Mapped[str] = mapped_column(String(128), default="system", index=True)
    source_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    source_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    suggestion_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    status: Mapped[str] = mapped_column(String(32), default="", index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    detail_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class KnowledgeOperationDraft(Base):
    """A draft knowledge asset created while handling an operation item."""

    __tablename__ = "knowledge_operation_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    draft_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("knowledge_operation_items.item_id", ondelete="CASCADE"),
        index=True,
    )
    knowledge_base_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("knowledge_bases.knowledge_base_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    doc_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("documents.doc_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    question_log_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("question_logs.question_log_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    draft_type: Mapped[str] = mapped_column(String(64), default="faq", index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    question: Mapped[str] = mapped_column(Text, default="")
    answer: Mapped[str] = mapped_column(Text, default="")
    source_note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(128), default="system", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
