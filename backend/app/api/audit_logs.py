"""Audit log API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse
from app.services import audit_log_service

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    knowledge_base_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    actor_id: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    """List audit logs with optional filters."""
    logs = audit_log_service.list_audit_logs(
        db,
        knowledge_base_id=knowledge_base_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        created_from=created_from,
        created_to=created_to,
    )
    return AuditLogListResponse(
        audit_logs=[AuditLogResponse.model_validate(log) for log in logs]
    )
