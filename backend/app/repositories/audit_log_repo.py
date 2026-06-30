"""Audit log repository."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog


def create_audit_log(db: Session, audit_log: AuditLog) -> AuditLog:
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def list_audit_logs(
    db: Session,
    *,
    knowledge_base_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    actor_id: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> list[AuditLog]:
    query = select(AuditLog)
    if knowledge_base_id:
        query = query.where(AuditLog.knowledge_base_id == knowledge_base_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)
    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)
    if created_from:
        query = query.where(AuditLog.created_at >= created_from)
    if created_to:
        query = query.where(AuditLog.created_at <= created_to)
    return list(db.scalars(query.order_by(AuditLog.created_at.desc())))
