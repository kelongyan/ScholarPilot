"""Governance schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

KnowledgeBaseMemberRole = Literal["viewer", "contributor", "manager", "owner"]
KnowledgeBaseMemberStatus = Literal["active", "disabled"]


class UserAccountResponse(BaseModel):
    """Public governance user account."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str = ""
    display_name: str = ""
    status: str = "active"
    role: str = "user"
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseMemberResponse(BaseModel):
    """Public knowledge-base member representation."""

    model_config = ConfigDict(from_attributes=True)

    membership_id: str
    knowledge_base_id: str
    user_id: str
    role: str
    status: str
    created_by: str = ""
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseMemberListResponse(BaseModel):
    """List of knowledge-base members."""

    members: list[KnowledgeBaseMemberResponse]


class KnowledgeBaseMemberUpsertRequest(BaseModel):
    """Create or update a knowledge-base member."""

    role: KnowledgeBaseMemberRole = Field(default="viewer")
    status: KnowledgeBaseMemberStatus = Field(default="active")
