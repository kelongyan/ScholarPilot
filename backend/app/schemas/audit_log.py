"""Audit log schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    """Public audit log representation."""

    model_config = ConfigDict(from_attributes=True)

    audit_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    knowledge_base_id: str | None = None
    detail_json: dict[str, object] = Field(default_factory=dict)
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """List of audit log records."""

    audit_logs: list[AuditLogResponse]
