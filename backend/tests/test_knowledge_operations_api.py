"""Tests for knowledge operations API routes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app
from app.schemas.knowledge_operations import KnowledgeOperationSuggestionResponse

client = TestClient(app)


def _fake_get_db():
    yield object()


def test_list_knowledge_operation_suggestions(monkeypatch) -> None:
    from app.services import knowledge_operations_service

    captured = {}

    def fake_list_suggestions(db, *, knowledge_base_id=None):
        captured["knowledge_base_id"] = knowledge_base_id
        return [
            KnowledgeOperationSuggestionResponse(
                suggestion_id="no-answer:ql-1",
                knowledge_base_id="kb-1",
                question_log_id="ql-1",
                suggestion_type="faq_draft",
                severity="high",
                title="Draft missing knowledge answer",
                description="Missing evidence.",
                suggested_action="Create an FAQ draft.",
                evidence=[{"question": "What is missing?"}],
                created_at=datetime(2026, 6, 30, tzinfo=UTC),
            )
        ]

    monkeypatch.setattr(
        knowledge_operations_service,
        "list_suggestions",
        fake_list_suggestions,
    )

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/knowledge-operations/suggestions",
            params={"knowledge_base_id": "kb-1"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert captured["knowledge_base_id"] == "kb-1"
    body = response.json()
    assert body["suggestions"][0]["suggestion_id"] == "no-answer:ql-1"
    assert body["suggestions"][0]["suggestion_type"] == "faq_draft"
