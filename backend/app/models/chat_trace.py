"""Persisted chat trace ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ChatTrace(Base):
    """Persisted retrieval trace for a chat answer."""

    __tablename__ = "chat_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    trace_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    question_log_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("question_logs.question_log_id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    query: Mapped[str] = mapped_column(Text, default="")
    rewritten_query: Mapped[str] = mapped_column(Text, default="")
    dense_results_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    sparse_results_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    fused_results_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    reranked_results_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    evidence_pack_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    answer: Mapped[str] = mapped_column(Text, default="")
    citations_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    answer_status: Mapped[str] = mapped_column(String(32), default="answered", index=True)
    model: Mapped[str] = mapped_column(String(128), default="")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
