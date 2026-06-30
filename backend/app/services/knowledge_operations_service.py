"""Knowledge operations suggestion generation.

This first slice is deterministic: it turns existing question logs, feedback,
and failed documents into draft improvement suggestions. It intentionally avoids
new orchestration dependencies so the product loop can stabilize before adding
an LLM-backed operations agent.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories import document_repo, question_log_repo
from app.schemas.knowledge_operations import KnowledgeOperationSuggestionResponse


def list_suggestions(
    db: Session,
    *,
    knowledge_base_id: str | None = None,
) -> list[KnowledgeOperationSuggestionResponse]:
    """Build pending knowledge operations suggestions from existing signals."""
    suggestions: list[KnowledgeOperationSuggestionResponse] = []
    question_logs = [
        log
        for log in question_log_repo.list_question_logs(db)
        if _matches_knowledge_base(log.knowledge_base_id, knowledge_base_id)
    ]
    feedback_by_question_log_id = {
        feedback.question_log_id: feedback
        for feedback in question_log_repo.list_answer_feedback(db)
    }

    for log in question_logs:
        if log.answer_status != "answered":
            suggestions.append(_no_answer_suggestion(log))
            continue

        feedback = feedback_by_question_log_id.get(log.question_log_id)
        if feedback and feedback.useful is False:
            suggestions.append(_poor_answer_suggestion(log, feedback))
        elif feedback and feedback.citation_accurate is False:
            suggestions.append(_citation_review_suggestion(log, feedback))

    for doc in document_repo.list_documents(db):
        if not _matches_knowledge_base(doc.knowledge_base_id, knowledge_base_id):
            continue
        if doc.status == "failed":
            suggestions.append(_failed_document_suggestion(doc))

    return sorted(
        suggestions,
        key=lambda item: (
            _severity_rank(item.severity),
            item.created_at is None,
            item.created_at,
        ),
        reverse=True,
    )


def _matches_knowledge_base(
    item_knowledge_base_id: str | None,
    requested_knowledge_base_id: str | None,
) -> bool:
    if requested_knowledge_base_id is None:
        return True
    return item_knowledge_base_id == requested_knowledge_base_id


def _no_answer_suggestion(log) -> KnowledgeOperationSuggestionResponse:
    return KnowledgeOperationSuggestionResponse(
        suggestion_id=f"no-answer:{log.question_log_id}",
        knowledge_base_id=log.knowledge_base_id,
        doc_id=log.doc_id,
        question_log_id=log.question_log_id,
        suggestion_type="faq_draft",
        severity="high",
        title="Draft missing knowledge answer",
        description=(
            "A question could not be answered from the indexed evidence. "
            "This is a candidate knowledge gap."
        ),
        suggested_action=(
            "Create an FAQ draft or upload source material that answers this question."
        ),
        evidence=[
            {
                "question": log.question,
                "answer_status": log.answer_status,
            }
        ],
        created_at=log.created_at,
    )


def _poor_answer_suggestion(log, feedback) -> KnowledgeOperationSuggestionResponse:
    return KnowledgeOperationSuggestionResponse(
        suggestion_id=f"poor-answer:{feedback.feedback_id}",
        knowledge_base_id=log.knowledge_base_id,
        doc_id=log.doc_id,
        question_log_id=log.question_log_id,
        suggestion_type="answer_quality_review",
        severity="medium",
        title="Review answer marked not useful",
        description="A user marked this answer as not useful.",
        suggested_action=(
            "Review the answer, citations, and source coverage before updating the "
            "knowledge base."
        ),
        evidence=[
            {
                "question": log.question,
                "useful": feedback.useful,
                "citation_accurate": feedback.citation_accurate,
            }
        ],
        created_at=feedback.created_at,
    )


def _citation_review_suggestion(log, feedback) -> KnowledgeOperationSuggestionResponse:
    return KnowledgeOperationSuggestionResponse(
        suggestion_id=f"citation-review:{feedback.feedback_id}",
        knowledge_base_id=log.knowledge_base_id,
        doc_id=log.doc_id,
        question_log_id=log.question_log_id,
        suggestion_type="citation_review",
        severity="medium",
        title="Review inaccurate citation feedback",
        description="A user reported that the answer citation was inaccurate.",
        suggested_action=(
            "Inspect the cited chunks and improve source documents or retrieval settings."
        ),
        evidence=[
            {
                "question": log.question,
                "useful": feedback.useful,
                "citation_accurate": feedback.citation_accurate,
            }
        ],
        created_at=feedback.created_at,
    )


def _failed_document_suggestion(doc) -> KnowledgeOperationSuggestionResponse:
    return KnowledgeOperationSuggestionResponse(
        suggestion_id=f"failed-document:{doc.doc_id}",
        knowledge_base_id=doc.knowledge_base_id,
        doc_id=doc.doc_id,
        suggestion_type="reindex_document",
        severity="high",
        title="Fix failed document processing",
        description="A source document failed parsing, embedding, or indexing.",
        suggested_action=(
            "Inspect the error, replace the source file if needed, then reindex the document."
        ),
        evidence=[
            {
                "title": doc.title,
                "status": doc.status,
                "error_message": doc.error_message,
            }
        ],
        created_at=doc.updated_at,
    )


def _severity_rank(severity: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(severity, 0)
