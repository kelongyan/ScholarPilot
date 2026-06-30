"""Knowledge operations API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import (
    CurrentUser,
    filter_by_knowledge_base_access,
    require_knowledge_base_access,
    require_min_role,
)
from app.core.db import get_db
from app.schemas.knowledge_operations import (
    KnowledgeOperationItemListResponse,
    KnowledgeOperationItemResponse,
    KnowledgeOperationItemUpdateRequest,
    KnowledgeOperationSuggestionListResponse,
)
from app.services import audit_log_service, knowledge_operations_service

router = APIRouter(prefix="/knowledge-operations", tags=["knowledge-operations"])


@router.get("/items", response_model=KnowledgeOperationItemListResponse)
async def list_items(
    knowledge_base_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeOperationItemListResponse:
    """List persisted knowledge operation items."""
    require_knowledge_base_access(current_user, knowledge_base_id)
    items = knowledge_operations_service.list_items(
        db,
        knowledge_base_id=knowledge_base_id,
        status=status,
    )
    items = filter_by_knowledge_base_access(
        items,
        current_user,
        get_knowledge_base_id=lambda item: item.knowledge_base_id,
    )
    return KnowledgeOperationItemListResponse(
        items=[KnowledgeOperationItemResponse.model_validate(item) for item in items]
    )


@router.patch("/items/{item_id}", response_model=KnowledgeOperationItemResponse)
async def update_item(
    item_id: str,
    request: KnowledgeOperationItemUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeOperationItemResponse:
    """Update handling status for a knowledge operation item."""
    item = knowledge_operations_service.update_item(
        db,
        item_id,
        status=request.status,
        resolution_note=request.resolution_note,
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge operation item not found: {item_id}",
        )
    require_knowledge_base_access(current_user, item.knowledge_base_id)
    audit_log_service.try_log_event(
        db,
        action="knowledge_operation_item.updated",
        resource_type="knowledge_operation_item",
        resource_id=item.item_id,
        knowledge_base_id=item.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={
            "status": item.status,
            "resolution_note": item.resolution_note,
            "source_type": item.source_type,
            "source_id": item.source_id,
            "suggestion_type": item.suggestion_type,
            "doc_id": item.doc_id,
            "question_log_id": item.question_log_id,
        },
    )
    return KnowledgeOperationItemResponse.model_validate(item)


@router.get("/suggestions", response_model=KnowledgeOperationSuggestionListResponse)
async def list_suggestions(
    knowledge_base_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeOperationSuggestionListResponse:
    """List generated knowledge operations suggestions."""
    require_knowledge_base_access(current_user, knowledge_base_id)
    suggestions = knowledge_operations_service.list_suggestions(
        db,
        knowledge_base_id=knowledge_base_id,
    )
    suggestions = [
        suggestion
        for suggestion in suggestions
        if current_user.can_access_knowledge_base(suggestion.knowledge_base_id)
    ]
    return KnowledgeOperationSuggestionListResponse(suggestions=suggestions)
