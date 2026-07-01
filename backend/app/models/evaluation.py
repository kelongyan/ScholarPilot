"""Evaluation dataset and run ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class EvaluationDataset(Base):
    """A fixed or curated set of evaluation questions."""

    __tablename__ = "evaluation_datasets"

    dataset_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    source_uri: Mapped[str] = mapped_column(String(512), default="")
    questions_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class EvaluationRun(Base):
    """A persisted evaluation execution over a dataset."""

    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    dataset_key: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("evaluation_datasets.dataset_key", ondelete="RESTRICT"),
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
    execution_mode: Mapped[str] = mapped_column(String(16), default="chat", index=True)
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    passed_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    average_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    dataset_version: Mapped[str] = mapped_column(String(64), default="")
    config_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    summary_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    metrics_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class EvaluationRunItem(Base):
    """A single evaluated question and its artifacts."""

    __tablename__ = "evaluation_run_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    question: Mapped[str] = mapped_column(Text, default="")
    expected_keywords_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    matched_keywords_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_keywords_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    metrics_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    answer: Mapped[str] = mapped_column(Text, default="")
    answer_status: Mapped[str] = mapped_column(String(32), default="")
    execution_route: Mapped[str] = mapped_column(String(32), default="")
    status: Mapped[str] = mapped_column(String(16), default="passed", index=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
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
    agent_run_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("agent_runs.run_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
