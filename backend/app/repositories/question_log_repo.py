"""Question log repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AnswerFeedback, QuestionLog


def create_question_log(db: Session, question_log: QuestionLog) -> QuestionLog:
    db.add(question_log)
    db.commit()
    db.refresh(question_log)
    return question_log


def get_question_log(db: Session, question_log_id: str) -> QuestionLog | None:
    return db.scalar(
        select(QuestionLog).where(QuestionLog.question_log_id == question_log_id)
    )


def list_question_logs(db: Session) -> list[QuestionLog]:
    return list(db.scalars(select(QuestionLog).order_by(QuestionLog.created_at.desc())))


def list_answer_feedback(db: Session) -> list[AnswerFeedback]:
    return list(
        db.scalars(select(AnswerFeedback).order_by(AnswerFeedback.created_at.desc()))
    )


def create_answer_feedback(db: Session, feedback: AnswerFeedback) -> AnswerFeedback:
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_feedback_by_question_log(
    db: Session, question_log_id: str
) -> AnswerFeedback | None:
    return db.scalar(
        select(AnswerFeedback).where(AnswerFeedback.question_log_id == question_log_id)
    )


def update_answer_feedback(
    db: Session,
    feedback: AnswerFeedback,
    *,
    useful: bool | None = None,
    citation_accurate: bool | None = None,
) -> AnswerFeedback:
    if useful is not None:
        feedback.useful = useful
    if citation_accurate is not None:
        feedback.citation_accurate = citation_accurate
    db.commit()
    db.refresh(feedback)
    return feedback
