"""Governance repositories."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeBaseMember, UserAccount


def create_user_account(db: Session, user: UserAccount) -> UserAccount:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_account(db: Session, user_id: str) -> UserAccount | None:
    return db.scalar(select(UserAccount).where(UserAccount.user_id == user_id))


def list_user_accounts(db: Session) -> list[UserAccount]:
    return list(db.scalars(select(UserAccount).order_by(UserAccount.created_at.desc())))


def update_user_account(
    db: Session,
    user: UserAccount,
    *,
    email: str | None = None,
    display_name: str | None = None,
    status: str | None = None,
    role: str | None = None,
) -> UserAccount:
    if email is not None:
        user.email = email
    if display_name is not None:
        user.display_name = display_name
    if status is not None:
        user.status = status
    if role is not None:
        user.role = role
    db.commit()
    db.refresh(user)
    return user


def create_member(db: Session, member: KnowledgeBaseMember) -> KnowledgeBaseMember:
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def get_member(
    db: Session,
    *,
    knowledge_base_id: str,
    user_id: str,
) -> KnowledgeBaseMember | None:
    return db.scalar(
        select(KnowledgeBaseMember).where(
            KnowledgeBaseMember.knowledge_base_id == knowledge_base_id,
            KnowledgeBaseMember.user_id == user_id,
        )
    )


def list_members(
    db: Session,
    *,
    knowledge_base_id: str,
) -> list[KnowledgeBaseMember]:
    return list(
        db.scalars(
            select(KnowledgeBaseMember)
            .where(KnowledgeBaseMember.knowledge_base_id == knowledge_base_id)
            .order_by(KnowledgeBaseMember.created_at.desc())
        )
    )


def has_memberships(
    db: Session,
    *,
    knowledge_base_id: str,
) -> bool:
    return (
        db.scalar(
            select(KnowledgeBaseMember.id)
            .where(KnowledgeBaseMember.knowledge_base_id == knowledge_base_id)
            .limit(1)
        )
        is not None
    )


def update_member(
    db: Session,
    member: KnowledgeBaseMember,
    *,
    role: str | None = None,
    status: str | None = None,
) -> KnowledgeBaseMember:
    if role is not None:
        member.role = role
    if status is not None:
        member.status = status
    db.commit()
    db.refresh(member)
    return member
