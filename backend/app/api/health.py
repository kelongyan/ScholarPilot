"""Health check route."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe.

    Returns ``{"status": "ok"}`` when the API process is up. Deeper dependency
    checks (database, vector store, Redis) are added in Phase 1.
    """
    return {"status": "ok"}
