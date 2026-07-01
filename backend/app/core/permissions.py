"""Membership-aware permission helpers for API routes."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.services import governance_service
from app.services.governance_service import KnowledgeBaseMemberRole


def require_knowledge_base_access(
    db: Session,
    current_user: CurrentUser,
    knowledge_base_id: str | None,
    *,
    min_member_role: KnowledgeBaseMemberRole = "viewer",
) -> None:
    if not governance_service.can_access_knowledge_base(
        db,
        current_user,
        knowledge_base_id,
        min_member_role=min_member_role,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Knowledge base access denied.",
        )


def filter_by_knowledge_base_access[T](
    db: Session,
    items: list[T],
    current_user: CurrentUser,
    *,
    get_knowledge_base_id: Callable[[T], str | None],
    min_member_role: KnowledgeBaseMemberRole = "viewer",
) -> list[T]:
    return governance_service.filter_by_knowledge_base_access(
        db,
        items,
        current_user,
        get_knowledge_base_id=get_knowledge_base_id,
        min_member_role=min_member_role,
    )
