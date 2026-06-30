"""Authentication introspection API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import CurrentUser, get_current_user
from app.schemas.auth import CurrentUserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUserResponse:
    """Return the current actor and coarse RBAC scope."""
    return CurrentUserResponse(
        actor_id=current_user.actor_id,
        role=current_user.role,
        knowledge_base_ids=(
            sorted(current_user.knowledge_base_ids)
            if current_user.knowledge_base_ids is not None
            else None
        ),
        auth_enabled=current_user.auth_enabled,
    )
