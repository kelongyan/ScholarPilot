"""HTTP API routes."""

from app.api.audit_logs import router as audit_logs_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.chat_traces import router as chat_traces_router
from app.api.documents import router as documents_router
from app.api.evaluations import router as evaluations_router
from app.api.health import router as health_router
from app.api.knowledge_bases import router as knowledge_bases_router
from app.api.knowledge_operations import router as knowledge_operations_router
from app.api.question_logs import router as question_logs_router

__all__ = [
    "audit_logs_router",
    "auth_router",
    "chat_router",
    "chat_traces_router",
    "documents_router",
    "evaluations_router",
    "health_router",
    "knowledge_bases_router",
    "knowledge_operations_router",
    "question_logs_router",
]
