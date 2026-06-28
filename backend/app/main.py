"""FastAPI application entry point.

Run locally with::

    uv run uvicorn app.main:app --reload

The API is served at http://localhost:8000. The interactive docs are at
``/docs`` (Swagger) and ``/redoc`` (ReDoc).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Research Copilot for paper reading, evidence-first retrieval, "
    "and citation-grounded question answering.",
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


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with a short service description."""
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
