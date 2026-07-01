"""FastAPI application entry point.

Run locally with::

    uv run uvicorn app.main:app --reload

The API is served at http://localhost:8000. The interactive docs are at
``/docs`` (Swagger) and ``/redoc`` (ReDoc).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent_runs import router as agent_runs_router
from app.api.audit_logs import router as audit_logs_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.chat_traces import router as chat_traces_router
from app.api.documents import router as documents_router
from app.api.evaluations import router as evaluations_router
from app.api.governance import router as governance_router
from app.api.health import router as health_router
from app.api.knowledge_bases import router as knowledge_bases_router
from app.api.knowledge_operations import router as knowledge_operations_router
from app.api.observability import router as observability_router
from app.api.question_logs import router as question_logs_router
from app.core import get_settings
from app.core.qdrant import ensure_collection

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure the Qdrant collection exists on startup."""
    try:
        ensure_collection()
    except Exception:  # noqa: BLE001
        # Qdrant may not be up yet; the worker will create the collection on
        # first use. Don't block app startup.
        pass
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Verifiable team knowledge-base Q&A and knowledge operations API.",
    lifespan=lifespan,
)

# Allow the Next.js dev server to call the API. Tighten this in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(governance_router)
app.include_router(knowledge_bases_router)
app.include_router(knowledge_operations_router)
app.include_router(observability_router)
app.include_router(audit_logs_router)
app.include_router(evaluations_router)
app.include_router(chat_traces_router)
app.include_router(question_logs_router)
app.include_router(agent_runs_router)
app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with a short service description."""
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
