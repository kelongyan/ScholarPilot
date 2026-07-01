"""Governance API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, require_min_role
from app.core.db import get_db
from app.core.permissions import require_knowledge_base_access
from app.repositories import knowledge_base_repo
from app.schemas.governance import (
    KnowledgeBaseMemberListResponse,
    KnowledgeBaseMemberResponse,
    KnowledgeBaseMemberUpsertRequest,
    UserAccountResponse,
)
from app.services import audit_log_service, governance_service

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/users/me", response_model=UserAccountResponse)
async def get_current_governance_user(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("user")),
) -> UserAccountResponse:
    """Return or create the current actor's governance user record."""
    user = governance_service.ensure_current_user_account(db, current_user)
    return UserAccountResponse.model_validate(user)


@router.get(
    "/knowledge-bases/{knowledge_base_id}/members",
    response_model=KnowledgeBaseMemberListResponse,
)
async def list_knowledge_base_members(
    knowledge_base_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeBaseMemberListResponse:
    """List members for a knowledge base."""
    _require_existing_knowledge_base(db, knowledge_base_id)
    require_knowledge_base_access(
        db,
        current_user,
        knowledge_base_id,
        min_member_role="manager",
    )
    members = governance_service.list_knowledge_base_members(
        db,
        knowledge_base_id=knowledge_base_id,
    )
    return KnowledgeBaseMemberListResponse(
        members=[KnowledgeBaseMemberResponse.model_validate(member) for member in members]
    )


@router.put(
    "/knowledge-bases/{knowledge_base_id}/members/{user_id}",
    response_model=KnowledgeBaseMemberResponse,
)
async def upsert_knowledge_base_member(
    knowledge_base_id: str,
    user_id: str,
    request: KnowledgeBaseMemberUpsertRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> KnowledgeBaseMemberResponse:
    """Create or update a knowledge-base member."""
    _require_existing_knowledge_base(db, knowledge_base_id)
    require_knowledge_base_access(
        db,
        current_user,
        knowledge_base_id,
        min_member_role="owner",
    )
    member = governance_service.upsert_knowledge_base_member(
        db,
        knowledge_base_id=knowledge_base_id,
        user_id=user_id,
        role=request.role,
        status=request.status,
        actor_id=current_user.actor_id,
    )
    audit_log_service.try_log_event(
        db,
        action="knowledge_base_member.upserted",
        resource_type="knowledge_base_member",
        resource_id=member.membership_id,
        knowledge_base_id=knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={
            "user_id": member.user_id,
            "role": member.role,
            "status": member.status,
        },
    )
    return KnowledgeBaseMemberResponse.model_validate(member)


def _require_existing_knowledge_base(db: Session, knowledge_base_id: str) -> None:
    if knowledge_base_repo.get_knowledge_base(db, knowledge_base_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {knowledge_base_id}",
        )
