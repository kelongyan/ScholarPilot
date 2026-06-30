"""Persisted controlled Agent run ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class AgentRun(Base):
    """A persisted Phase 5 controlled Agent workflow run."""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    question_log_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("question_logs.question_log_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chat_trace_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("chat_traces.trace_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    doc_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("documents.doc_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    knowledge_base_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("knowledge_bases.knowledge_base_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, default="")
    route: Mapped[str] = mapped_column(String(32), default="short", index=True)
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True)
    answer_status: Mapped[str] = mapped_column(String(32), default="answered", index=True)
    answer: Mapped[str] = mapped_column(Text, default="")
    citations_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    trace_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    total_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class AgentStep(Base):
    """A persisted step inside a controlled Agent workflow run."""

    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    step_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("agent_runs.run_id", ondelete="CASCADE"),
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    agent_name: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True)
    input_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    output_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
