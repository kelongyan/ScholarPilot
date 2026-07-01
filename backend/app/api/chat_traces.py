"""Chat trace API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import (
    CurrentUser,
    require_min_role,
)
from app.core.db import get_db
from app.core.permissions import require_knowledge_base_access
from app.schemas.chat_trace import ChatTraceListResponse, ChatTraceResponse
from app.services import chat_trace_service, question_log_service

router = APIRouter(prefix="/chat-traces", tags=["chat-traces"])


@router.get("", response_model=ChatTraceListResponse)
async def list_chat_traces(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("admin")),
) -> ChatTraceListResponse:
    _ = current_user
    traces = chat_trace_service.list_chat_traces(db)
    return ChatTraceListResponse(
        chat_traces=[ChatTraceResponse.model_validate(trace) for trace in traces]
    )


@router.get("/{trace_id}", response_model=ChatTraceResponse)
async def get_chat_trace(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> ChatTraceResponse:
    trace = chat_trace_service.get_chat_trace(db, trace_id)
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat trace not found: {trace_id}",
        )
    question_log = question_log_service.get_question_log(db, trace.question_log_id)
    if question_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question log not found for trace: {trace_id}",
        )
    require_knowledge_base_access(db, current_user, question_log.knowledge_base_id)
    return ChatTraceResponse.model_validate(trace)
