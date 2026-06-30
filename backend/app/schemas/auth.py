"""Authentication and RBAC schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.auth import UserRole


class CurrentUserResponse(BaseModel):
    """Current authenticated actor and coarse-grained authorization scope."""

    actor_id: str
    role: UserRole
    knowledge_base_ids: list[str] | None = Field(default=None)
    auth_enabled: bool
