"""Knowledge operations API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import (
    CurrentUser,
    require_min_role,
)
from app.core.db import get_db
from app.core.permissions import (
    filter_by_knowledge_base_access,
    require_knowledge_base_access,
)
from app.repositories import agent_run_repo
from app.schemas.knowledge_operations import (
    KnowledgeOperationDraftListResponse,
    KnowledgeOperationDraftResponse,
    KnowledgeOperationEventListResponse,
    KnowledgeOperationEventResponse,
    KnowledgeOperationItemListResponse,
    KnowledgeOperationItemResponse,
    KnowledgeOperationItemUpdateRequest,
    KnowledgeOperationSuggestionListResponse,
    KnowledgeOperationSuggestionResponse,
)
from app.services import audit_log_service, knowledge_operations_service

router = APIRouter(prefix="/knowledge-operations", tags=["knowledge-operations"])


@router.get("/items", response_model=KnowledgeOperationItemListResponse)
async def list_items(
    knowledge_base_id: str | None = None,
    status: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeOperationItemListResponse:
    """List persisted knowledge operation items."""
    require_knowledge_base_access(
        db,
        current_user,
        knowledge_base_id,
        min_member_role="manager",
    )
    items = knowledge_operations_service.list_items(
        db,
        knowledge_base_id=knowledge_base_id,
        status=status,
        source_type=source_type,
        source_id=source_id,
    )
    items = filter_by_knowledge_base_access(
        db,
        items,
        current_user,
        get_knowledge_base_id=lambda item: item.knowledge_base_id,
        min_member_role="manager",
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
    existing = knowledge_operations_service.get_item(db, item_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge operation item not found: {item_id}",
        )
    require_knowledge_base_access(
        db,
        current_user,
        existing.knowledge_base_id,
        min_member_role="manager",
    )
    try:
        item = knowledge_operations_service.update_item(
            db,
            item_id,
            status=request.status,
            resolution_note=request.resolution_note,
            actor_id=current_user.actor_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge operation item not found: {item_id}",
        )
    require_knowledge_base_access(
        db,
        current_user,
        item.knowledge_base_id,
        min_member_role="manager",
    )
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


@router.get("/drafts", response_model=KnowledgeOperationDraftListResponse)
async def list_drafts(
    knowledge_base_id: str | None = None,
    item_id: str | None = None,
    draft_status: Annotated[str | None, Query(alias="status")] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeOperationDraftListResponse:
    """List draft knowledge assets created from operation handling."""
    require_knowledge_base_access(
        db,
        current_user,
        knowledge_base_id,
        min_member_role="manager",
    )
    if item_id is not None:
        item = knowledge_operations_service.get_item(db, item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge operation item not found: {item_id}",
            )
        require_knowledge_base_access(
            db,
            current_user,
            item.knowledge_base_id,
            min_member_role="manager",
        )
    drafts = knowledge_operations_service.list_drafts(
        db,
        knowledge_base_id=knowledge_base_id,
        item_id=item_id,
        status=draft_status,
    )
    drafts = [
        draft
        for draft in drafts
        if governance_access(db, current_user, draft.knowledge_base_id)
    ]
    return KnowledgeOperationDraftListResponse(
        drafts=[KnowledgeOperationDraftResponse.model_validate(draft) for draft in drafts]
    )


@router.get("/items/{item_id}/events", response_model=KnowledgeOperationEventListResponse)
async def list_item_events(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeOperationEventListResponse:
    """List structured lifecycle events for a knowledge operation item."""
    item = knowledge_operations_service.get_item(db, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge operation item not found: {item_id}",
        )
    require_knowledge_base_access(
        db,
        current_user,
        item.knowledge_base_id,
        min_member_role="manager",
    )
    events = knowledge_operations_service.list_item_events(db, item_id=item_id)
    events = [
        event
        for event in events
        if governance_access(db, current_user, event.knowledge_base_id)
    ]
    return KnowledgeOperationEventListResponse(
        events=[KnowledgeOperationEventResponse.model_validate(event) for event in events]
    )


@router.get("/suggestions", response_model=KnowledgeOperationSuggestionListResponse)
async def list_suggestions(
    knowledge_base_id: str | None = None,
    run_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeOperationSuggestionListResponse:
    """List generated knowledge operations suggestions."""
    if run_id is not None:
        run = agent_run_repo.get_agent_run(db, run_id)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent run not found: {run_id}",
            )
        require_knowledge_base_access(
            db,
            current_user,
            run.knowledge_base_id,
            min_member_role="manager",
        )
        suggestions = knowledge_operations_service.list_run_suggestions(db, run_id=run_id)
    else:
        require_knowledge_base_access(
            db,
            current_user,
            knowledge_base_id,
            min_member_role="manager",
        )
        suggestions = knowledge_operations_service.list_suggestions(
            db,
            knowledge_base_id=knowledge_base_id,
        )
    suggestions = [
        KnowledgeOperationSuggestionResponse.model_validate(suggestion)
        for suggestion in suggestions
        if governance_access(db, current_user, suggestion.knowledge_base_id)
    ]
    return KnowledgeOperationSuggestionListResponse(suggestions=suggestions)


def governance_access(
    db: Session,
    current_user: CurrentUser,
    knowledge_base_id: str | None,
) -> bool:
    from app.services import governance_service

    return governance_service.can_access_knowledge_base(
        db,
        current_user,
        knowledge_base_id,
        min_member_role="manager",
    )
