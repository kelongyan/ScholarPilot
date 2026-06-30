"""Data access repositories."""

from app.repositories import chat_trace_repo, document_repo, knowledge_base_repo, question_log_repo

__all__ = [
    "chat_trace_repo",
    "document_repo",
    "knowledge_base_repo",
    "question_log_repo",
]
