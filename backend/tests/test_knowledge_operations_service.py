"""Tests for generated knowledge operations suggestions."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services import knowledge_operations_service


class _QuestionLog:
    question_log_id = "ql-1"
    doc_id = "doc-1"
    knowledge_base_id = "kb-1"
    question = "How do we handle incident escalation?"
    answer_status = "insufficient_evidence"
    created_at = datetime(2026, 6, 30, tzinfo=UTC)


class _AnsweredQuestionLog:
    question_log_id = "ql-2"
    doc_id = "doc-2"
    knowledge_base_id = "kb-1"
    question = "What is the owner assignment policy?"
    answer_status = "answered"
    created_at = datetime(2026, 6, 30, tzinfo=UTC)


class _Feedback:
    feedback_id = "fb-1"
    question_log_id = "ql-2"
    useful = False
    citation_accurate = False
    created_at = datetime(2026, 6, 30, tzinfo=UTC)


class _FailedDocument:
    doc_id = "doc-3"
    knowledge_base_id = "kb-1"
    title = "Broken source"
    status = "failed"
    error_message = "parse error"
    updated_at = datetime(2026, 6, 30, tzinfo=UTC)


def test_list_suggestions_builds_operations_items(monkeypatch) -> None:
    from app.repositories import document_repo, question_log_repo

    monkeypatch.setattr(
        question_log_repo,
        "list_question_logs",
        lambda db: [_QuestionLog(), _AnsweredQuestionLog()],
    )
    monkeypatch.setattr(
        question_log_repo,
        "list_answer_feedback",
        lambda db: [_Feedback()],
    )
    monkeypatch.setattr(
        document_repo,
        "list_documents",
        lambda db: [_FailedDocument()],
    )

    suggestions = knowledge_operations_service.list_suggestions(
        object(),
        knowledge_base_id="kb-1",
    )

    assert {item.suggestion_type for item in suggestions} == {
        "faq_draft",
        "answer_quality_review",
        "reindex_document",
    }
    assert all(item.knowledge_base_id == "kb-1" for item in suggestions)


def test_list_suggestions_filters_by_knowledge_base(monkeypatch) -> None:
    from app.repositories import document_repo, question_log_repo

    monkeypatch.setattr(question_log_repo, "list_question_logs", lambda db: [_QuestionLog()])
    monkeypatch.setattr(question_log_repo, "list_answer_feedback", lambda db: [])
    monkeypatch.setattr(document_repo, "list_documents", lambda db: [])

    suggestions = knowledge_operations_service.list_suggestions(
        object(),
        knowledge_base_id="other-kb",
    )

    assert suggestions == []
