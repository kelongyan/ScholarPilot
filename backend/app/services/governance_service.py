"""Governance service for users and knowledge-base memberships."""

from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.models import KnowledgeBaseMember, UserAccount
from app.repositories import governance_repo

KnowledgeBaseMemberRole = Literal["viewer", "contributor", "manager", "owner"]
KnowledgeBaseMemberStatus = Literal["active", "disabled"]

_MEMBER_ROLE_RANK: dict[str, int] = {
    "viewer": 1,
    "contributor": 2,
    "manager": 3,
    "owner": 4,
}


def ensure_user_account(
    db: Session,
    *,
    user_id: str,
    role: str = "user",
    email: str = "",
    display_name: str = "",
) -> UserAccount:
    """Create a user account record if one does not already exist."""
    existing = governance_repo.get_user_account(db, user_id)
    if existing is not None:
        return existing
    return governance_repo.create_user_account(
        db,
        UserAccount(
            user_id=user_id,
            role=role,
            email=email,
            display_name=display_name or user_id,
            status="active",
        ),
    )


def ensure_current_user_account(db: Session, current_user: CurrentUser) -> UserAccount:
    """Persist the authenticated actor as a governance user account."""
    return ensure_user_account(
        db,
        user_id=current_user.actor_id,
        role=current_user.role,
        display_name=current_user.actor_id,
    )


def upsert_knowledge_base_member(
    db: Session,
    *,
    knowledge_base_id: str,
    user_id: str,
    role: KnowledgeBaseMemberRole,
    status: KnowledgeBaseMemberStatus = "active",
    actor_id: str = "",
) -> KnowledgeBaseMember:
    """Create or update a user's membership for a knowledge base."""
    ensure_user_account(db, user_id=user_id)
    existing = governance_repo.get_member(
        db,
        knowledge_base_id=knowledge_base_id,
        user_id=user_id,
    )
    if existing is not None:
        return governance_repo.update_member(
            db,
            existing,
            role=role,
            status=status,
        )
    return governance_repo.create_member(
        db,
        KnowledgeBaseMember(
            membership_id=str(uuid.uuid4()),
            knowledge_base_id=knowledge_base_id,
            user_id=user_id,
            role=role,
            status=status,
            created_by=actor_id,
        ),
    )


def list_knowledge_base_members(
    db: Session,
    *,
    knowledge_base_id: str,
) -> list[KnowledgeBaseMember]:
    return governance_repo.list_members(db, knowledge_base_id=knowledge_base_id)


def can_access_knowledge_base(
    db: Session,
    current_user: CurrentUser,
    knowledge_base_id: str | None,
    *,
    min_member_role: KnowledgeBaseMemberRole = "viewer",
) -> bool:
    """Return whether an actor can access a KB under membership-aware rules."""
    if current_user.role == "admin":
        return True
    if not knowledge_base_id:
        return current_user.can_access_knowledge_base(knowledge_base_id)

    membership = governance_repo.get_member(
        db,
        knowledge_base_id=knowledge_base_id,
        user_id=current_user.actor_id,
    )
    if membership is not None and membership.status == "active":
        return _member_role_allows(membership.role, min_member_role)
    if governance_repo.has_memberships(db, knowledge_base_id=knowledge_base_id):
        return False
    return current_user.can_access_knowledge_base(knowledge_base_id)


def filter_by_knowledge_base_access[T](
    db: Session,
    items: list[T],
    current_user: CurrentUser,
    *,
    get_knowledge_base_id,
    min_member_role: KnowledgeBaseMemberRole = "viewer",
) -> list[T]:
    """Filter items by membership-aware KB access."""
    return [
        item
        for item in items
        if can_access_knowledge_base(
            db,
            current_user,
            get_knowledge_base_id(item),
            min_member_role=min_member_role,
        )
    ]


def _member_role_allows(actual_role: str, required_role: str) -> bool:
    return _MEMBER_ROLE_RANK.get(actual_role, 0) >= _MEMBER_ROLE_RANK[required_role]
