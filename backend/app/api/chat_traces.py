"""Chat trace API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, require_min_role
from app.core.db import get_db
from app.schemas.chat_trace import ChatTraceListResponse, ChatTraceResponse
from app.services import chat_trace_service

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
    current_user: CurrentUser = Depends(require_min_role("admin")),
) -> ChatTraceResponse:
    _ = current_user
    trace = chat_trace_service.get_chat_trace(db, trace_id)
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat trace not found: {trace_id}",
        )
    return ChatTraceResponse.model_validate(trace)
