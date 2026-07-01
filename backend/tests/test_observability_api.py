"""Tests for observability API routes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app

client = TestClient(app)


def _fake_get_db():
    yield object()


def test_get_observability_summary(monkeypatch) -> None:
    from app.schemas.observability import ObservabilitySummaryResponse
    from app.services import observability_service

    captured = {}

    def fake_get_summary(db, **kwargs):
        captured.update(kwargs)
        return ObservabilitySummaryResponse(
            knowledge_base_id="kb-1",
            question_count=2,
            answered_count=1,
            unresolved_answer_count=1,
            no_answer_rate=0.5,
            generated_at=datetime(2026, 7, 1, tzinfo=UTC),
        )

    monkeypatch.setattr(observability_service, "get_summary", fake_get_summary)

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/observability/summary",
            params={"knowledge_base_id": "kb-1"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    body = response.json()
    assert body["knowledge_base_id"] == "kb-1"
    assert body["question_count"] == 2
    assert body["no_answer_rate"] == 0.5
    assert captured["knowledge_base_id"] == "kb-1"
    assert captured["allowed_knowledge_base_ids"] is None
