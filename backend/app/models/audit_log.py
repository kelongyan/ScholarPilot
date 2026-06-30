"""Audit log ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class AuditLog(Base):
    """An immutable user or system action record."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    audit_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    actor_id: Mapped[str] = mapped_column(String(128), default="system", index=True)
    action: Mapped[str] = mapped_column(String(128), default="", index=True)
    resource_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    resource_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    knowledge_base_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("knowledge_bases.knowledge_base_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    detail_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
