"""Audit log service."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AuditLog
from app.repositories import audit_log_repo

DEFAULT_ACTOR_ID = "system"


def log_event(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str,
    knowledge_base_id: str | None = None,
    actor_id: str = DEFAULT_ACTOR_ID,
    detail_json: dict[str, object] | None = None,
) -> AuditLog:
    """Persist one audit event."""
    return audit_log_repo.create_audit_log(
        db,
        AuditLog(
            audit_id=str(uuid.uuid4()),
            actor_id=actor_id or DEFAULT_ACTOR_ID,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            knowledge_base_id=knowledge_base_id,
            detail_json=detail_json or {},
        ),
    )


def try_log_event(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str,
    knowledge_base_id: str | None = None,
    actor_id: str = DEFAULT_ACTOR_ID,
    detail_json: dict[str, object] | None = None,
) -> AuditLog | None:
    """Persist one audit event without failing the primary workflow."""
    try:
        return log_event(
            db,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            knowledge_base_id=knowledge_base_id,
            actor_id=actor_id,
            detail_json=detail_json,
        )
    except Exception:  # noqa: BLE001
        rollback = getattr(db, "rollback", None)
        if callable(rollback):
            rollback()
        return None


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
    """List persisted audit events."""
    return audit_log_repo.list_audit_logs(
        db,
        knowledge_base_id=knowledge_base_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        created_from=created_from,
        created_to=created_to,
    )
