"""HTTP API routes."""

from app.api.chat import router as chat_router
from app.api.chat_traces import router as chat_traces_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.knowledge_bases import router as knowledge_bases_router
from app.api.question_logs import router as question_logs_router

__all__ = [
    "chat_router",
    "chat_traces_router",
    "documents_router",
    "health_router",
    "knowledge_bases_router",
    "question_logs_router",
]
