"""Observability API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, require_min_role
from app.core.db import get_db
from app.core.permissions import require_knowledge_base_access
from app.schemas.observability import ObservabilitySummaryResponse
from app.services import observability_service

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/summary", response_model=ObservabilitySummaryResponse)
async def get_observability_summary(
    knowledge_base_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> ObservabilitySummaryResponse:
    """Return a compact quality and operations summary."""
    require_knowledge_base_access(
        db,
        current_user,
        knowledge_base_id,
        min_member_role="manager",
    )
    allowed_knowledge_base_ids = (
        current_user.knowledge_base_ids if knowledge_base_id is None else None
    )
    return observability_service.get_summary(
        db,
        knowledge_base_id=knowledge_base_id,
        allowed_knowledge_base_ids=allowed_knowledge_base_ids,
    )
