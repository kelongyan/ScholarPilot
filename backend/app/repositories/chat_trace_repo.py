"""Chat trace repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatTrace


def create_chat_trace(db: Session, chat_trace: ChatTrace) -> ChatTrace:
    db.add(chat_trace)
    db.commit()
    db.refresh(chat_trace)
    return chat_trace


def get_chat_trace(db: Session, trace_id: str) -> ChatTrace | None:
    return db.scalar(select(ChatTrace).where(ChatTrace.trace_id == trace_id))


def get_chat_trace_by_question_log_id(
    db: Session, question_log_id: str
) -> ChatTrace | None:
    return db.scalar(
        select(ChatTrace).where(ChatTrace.question_log_id == question_log_id)
    )


def list_chat_traces(db: Session) -> list[ChatTrace]:
    return list(db.scalars(select(ChatTrace).order_by(ChatTrace.created_at.desc())))
