"""Knowledge base API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
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
from app.schemas.knowledge_base import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdateRequest,
)
from app.services import audit_log_service, governance_service, knowledge_base_service

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    request: KnowledgeBaseCreateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeBaseResponse:
    kb = knowledge_base_service.create_knowledge_base(
        db,
        name=request.name,
        description=request.description,
        status=request.status,
        owner_id=request.owner_id or current_user.actor_id,
        visibility=request.visibility,
    )
    governance_service.ensure_current_user_account(db, current_user)
    member = governance_service.upsert_knowledge_base_member(
        db,
        knowledge_base_id=kb.knowledge_base_id,
        user_id=current_user.actor_id,
        role="owner",
        actor_id=current_user.actor_id,
    )
    audit_log_service.try_log_event(
        db,
        action="knowledge_base.created",
        resource_type="knowledge_base",
        resource_id=kb.knowledge_base_id,
        knowledge_base_id=kb.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={
            "name": kb.name,
            "status": kb.status,
            "owner_id": kb.owner_id,
            "visibility": kb.visibility,
        },
    )
    audit_log_service.try_log_event(
        db,
        action="knowledge_base_member.upserted",
        resource_type="knowledge_base_member",
        resource_id=member.membership_id,
        knowledge_base_id=kb.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={
            "user_id": member.user_id,
            "role": member.role,
            "status": member.status,
            "source": "knowledge_base.created",
        },
    )
    return KnowledgeBaseResponse.model_validate(kb)


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("user")),
) -> KnowledgeBaseListResponse:
    bases = knowledge_base_service.list_knowledge_bases(db)
    bases = filter_by_knowledge_base_access(
        db,
        bases,
        current_user,
        get_knowledge_base_id=lambda kb: kb.knowledge_base_id,
    )
    return KnowledgeBaseListResponse(
        knowledge_bases=[KnowledgeBaseResponse.model_validate(kb) for kb in bases]
    )


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    knowledge_base_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("user")),
) -> KnowledgeBaseResponse:
    kb = knowledge_base_service.get_knowledge_base(db, knowledge_base_id)
    if kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {knowledge_base_id}",
        )
    require_knowledge_base_access(db, current_user, kb.knowledge_base_id)
    return KnowledgeBaseResponse.model_validate(kb)


@router.patch("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    knowledge_base_id: str,
    request: KnowledgeBaseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeBaseResponse:
    existing = knowledge_base_service.get_knowledge_base(db, knowledge_base_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {knowledge_base_id}",
        )
    require_knowledge_base_access(
        db,
        current_user,
        existing.knowledge_base_id,
        min_member_role="manager",
    )
    kb = knowledge_base_service.update_knowledge_base(
        db,
        knowledge_base_id,
        name=request.name,
        description=request.description,
        status=request.status,
        owner_id=request.owner_id,
        visibility=request.visibility,
    )
    if kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {knowledge_base_id}",
        )
    audit_log_service.try_log_event(
        db,
        action="knowledge_base.updated",
        resource_type="knowledge_base",
        resource_id=kb.knowledge_base_id,
        knowledge_base_id=kb.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={
            "name": kb.name,
            "status": kb.status,
            "owner_id": kb.owner_id,
            "visibility": kb.visibility,
        },
    )
    return KnowledgeBaseResponse.model_validate(kb)
