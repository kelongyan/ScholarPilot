"""Governance ORM models for users and knowledge-base memberships."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class UserAccount(Base):
    """Persisted user identity used by governance APIs."""

    __tablename__ = "user_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(256), default="", index=True)
    display_name: Mapped[str] = mapped_column(String(256), default="")
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    role: Mapped[str] = mapped_column(String(32), default="user", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class KnowledgeBaseMember(Base):
    """A user's membership and role inside a knowledge base."""

    __tablename__ = "knowledge_base_members"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_base_id",
            "user_id",
            name="uq_knowledge_base_members_kb_user",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    membership_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    knowledge_base_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("knowledge_bases.knowledge_base_id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("user_accounts.user_id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), default="viewer", index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_by: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
