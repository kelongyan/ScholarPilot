"""Knowledge operations API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.knowledge_operations import (
    KnowledgeOperationSuggestionListResponse,
    KnowledgeOperationSuggestionResponse,
)
from app.services import knowledge_operations_service

router = APIRouter(prefix="/knowledge-operations", tags=["knowledge-operations"])


@router.get("/suggestions", response_model=KnowledgeOperationSuggestionListResponse)
async def list_suggestions(
    knowledge_base_id: str | None = None,
    db: Session = Depends(get_db),
) -> KnowledgeOperationSuggestionListResponse:
    """List generated knowledge operations suggestions."""
    suggestions = knowledge_operations_service.list_suggestions(
        db,
        knowledge_base_id=knowledge_base_id,
    )
    return KnowledgeOperationSuggestionListResponse(
        suggestions=[
            KnowledgeOperationSuggestionResponse.model_validate(suggestion)
            for suggestion in suggestions
        ]
    )
