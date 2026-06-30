"""Question log and feedback API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.question_log import (
    AnswerFeedbackRequest,
    AnswerFeedbackResponse,
    QuestionLogCreateRequest,
    QuestionLogListResponse,
    QuestionLogResponse,
)
from app.services import audit_log_service, question_log_service

router = APIRouter(prefix="/question-logs", tags=["question-logs"])


@router.get("", response_model=QuestionLogListResponse)
async def list_question_logs(db: Session = Depends(get_db)) -> QuestionLogListResponse:
    logs = question_log_service.list_question_logs(db)
    return QuestionLogListResponse(
        question_logs=[QuestionLogResponse.model_validate(log) for log in logs]
    )


@router.post("", response_model=QuestionLogResponse, status_code=status.HTTP_201_CREATED)
async def create_question_log(
    request: QuestionLogCreateRequest,
    db: Session = Depends(get_db),
) -> QuestionLogResponse:
    log = question_log_service.create_question_log(
        db,
        doc_id=request.doc_id,
        knowledge_base_id=request.knowledge_base_id,
        question=request.question,
        answer=request.answer,
        answer_status=request.answer_status,
        citations_json=request.citations_json,
    )
    return QuestionLogResponse.model_validate(log)


@router.post("/{question_log_id}/feedback", response_model=AnswerFeedbackResponse)
async def upsert_feedback(
    question_log_id: str,
    request: AnswerFeedbackRequest,
    db: Session = Depends(get_db),
) -> AnswerFeedbackResponse:
    existing_log = question_log_service.get_question_log(db, question_log_id)
    if existing_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question log not found: {question_log_id}",
        )
    feedback = question_log_service.create_or_update_feedback(
        db,
        question_log_id=question_log_id,
        useful=request.useful,
        citation_accurate=request.citation_accurate,
    )
    audit_log_service.try_log_event(
        db,
        action="feedback.submitted",
        resource_type="answer_feedback",
        resource_id=feedback.feedback_id,
        knowledge_base_id=getattr(existing_log, "knowledge_base_id", None),
        detail_json={
            "question_log_id": question_log_id,
            "doc_id": getattr(existing_log, "doc_id", None),
            "useful": request.useful,
            "citation_accurate": request.citation_accurate,
        },
    )
    return AnswerFeedbackResponse.model_validate(feedback)
