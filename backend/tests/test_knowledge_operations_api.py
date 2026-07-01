"""Tests for knowledge operations API routes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app

client = TestClient(app)


class _FakeItem:
    item_id = "item-1"
    knowledge_base_id = "kb-1"
    doc_id = "doc-1"
    question_log_id = "ql-1"
    source_type = "question_log"
    source_id = "ql-1"
    suggestion_type = "faq_draft"
    aggregate_key = "kb-1|faq_draft|question|missing evidence"
    signal_count = 1
    last_signal_at = datetime(2026, 6, 30, tzinfo=UTC)
    severity = "high"
    title = "Draft missing knowledge answer"
    description = "Missing evidence."
    suggested_action = "Create an FAQ draft."
    status = "pending"
    resolution_note = ""
    created_at = datetime(2026, 6, 30, tzinfo=UTC)
    updated_at = datetime(2026, 6, 30, tzinfo=UTC)
    agent_run_id = None


class _FakeEvent:
    event_id = "event-1"
    item_id = "item-1"
    knowledge_base_id = "kb-1"
    event_type = "status_updated"
    actor_id = "dev-user"
    source_type = "question_log"
    source_id = "ql-1"
    suggestion_type = "faq_draft"
    status = "resolved"
    note = "Added missing FAQ."
    detail_json = {"status": "resolved"}
    created_at = datetime(2026, 6, 30, tzinfo=UTC)


class _FakeDraft:
    draft_id = "draft-1"
    item_id = "item-1"
    knowledge_base_id = "kb-1"
    doc_id = "doc-1"
    question_log_id = "ql-1"
    draft_type = "faq"
    status = "draft"
    title = "Draft FAQ"
    question = "Question log ql-1"
    answer = ""
    source_note = "source"
    created_by = "manager-1"
    created_at = datetime(2026, 6, 30, tzinfo=UTC)
    updated_at = datetime(2026, 6, 30, tzinfo=UTC)


def _fake_get_db():
    yield object()


def test_list_knowledge_operation_items(monkeypatch) -> None:
    from app.services import knowledge_operations_service

    captured = {}

    def fake_list_items(
        db,
        *,
        knowledge_base_id=None,
        status=None,
        source_type=None,
        source_id=None,
    ):
        captured["knowledge_base_id"] = knowledge_base_id
        captured["status"] = status
        captured["source_type"] = source_type
        captured["source_id"] = source_id
        return [_FakeItem()]

    monkeypatch.setattr(knowledge_operations_service, "list_items", fake_list_items)

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/knowledge-operations/items",
            params={
                "knowledge_base_id": "kb-1",
                "status": "pending",
                "source_type": "agent_run",
                "source_id": "run-1",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert captured == {
        "knowledge_base_id": "kb-1",
        "status": "pending",
        "source_type": "agent_run",
        "source_id": "run-1",
    }
    body = response.json()
    assert body["items"][0]["item_id"] == "item-1"
    assert body["items"][0]["status"] == "pending"


def test_update_knowledge_operation_item_status(monkeypatch) -> None:
    from app.services import knowledge_operations_service

    captured = {}

    class ResolvedItem(_FakeItem):
        status = "resolved"
        resolution_note = "Added missing FAQ."

    def fake_update_item(db, item_id, *, status, resolution_note, actor_id="system"):
        captured["item_id"] = item_id
        captured["status"] = status
        captured["resolution_note"] = resolution_note
        captured["actor_id"] = actor_id
        return ResolvedItem()

    monkeypatch.setattr(knowledge_operations_service, "get_item", lambda db, item_id: _FakeItem())
    monkeypatch.setattr(knowledge_operations_service, "update_item", fake_update_item)

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.patch(
            "/knowledge-operations/items/item-1",
            json={"status": "resolved", "resolution_note": "Added missing FAQ."},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert captured == {
        "item_id": "item-1",
        "status": "resolved",
        "resolution_note": "Added missing FAQ.",
        "actor_id": "system",
    }
    assert response.json()["status"] == "resolved"


def test_update_knowledge_operation_item_404(monkeypatch) -> None:
    from app.services import knowledge_operations_service

    monkeypatch.setattr(
        knowledge_operations_service,
        "get_item",
        lambda db, item_id: None,
    )

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.patch(
            "/knowledge-operations/items/missing",
            json={"status": "ignored", "resolution_note": ""},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 404


def test_update_knowledge_operation_item_action_conflict(monkeypatch) -> None:
    from app.services import knowledge_operations_service

    monkeypatch.setattr(knowledge_operations_service, "get_item", lambda db, item_id: _FakeItem())

    def fake_update_item(db, item_id, *, status, resolution_note, actor_id="system"):
        raise ValueError("Cannot reindex an operation item without a document id.")

    monkeypatch.setattr(knowledge_operations_service, "update_item", fake_update_item)

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.patch(
            "/knowledge-operations/items/item-1",
            json={"status": "reindexed", "resolution_note": ""},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 409
    assert "Cannot reindex" in response.json()["detail"]


def test_list_knowledge_operation_item_events(monkeypatch) -> None:
    from app.services import knowledge_operations_service

    monkeypatch.setattr(knowledge_operations_service, "get_item", lambda db, item_id: _FakeItem())
    monkeypatch.setattr(
        knowledge_operations_service,
        "list_item_events",
        lambda db, *, item_id: [_FakeEvent()],
    )

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get("/knowledge-operations/items/item-1/events")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["events"][0]["event_type"] == "status_updated"


def test_list_knowledge_operation_drafts(monkeypatch) -> None:
    from app.services import knowledge_operations_service

    monkeypatch.setattr(knowledge_operations_service, "get_item", lambda db, item_id: _FakeItem())
    monkeypatch.setattr(
        knowledge_operations_service,
        "list_drafts",
        lambda db, **kwargs: [_FakeDraft()],
    )

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/knowledge-operations/drafts",
            params={"knowledge_base_id": "kb-1", "item_id": "item-1", "status": "draft"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["drafts"][0]["draft_id"] == "draft-1"


def test_list_knowledge_operation_suggestions_uses_agent_run_items(monkeypatch) -> None:
    from app.api import knowledge_operations as knowledge_operations_api
    from app.services import knowledge_operations_service

    called = {}

    class FakeRun:
        knowledge_base_id = "kb-1"

    class Suggestion:
        suggestion_id = "item-1"
        item_id = "item-1"
        knowledge_base_id = "kb-1"
        doc_id = "doc-1"
        question_log_id = "ql-1"
        agent_run_id = "run-1"
        source_type = "agent_run"
        source_id = "run-1"
        suggestion_type = "agent_review"
        aggregate_key = "kb-1|agent_review|agent_run|run-1"
        signal_count = 1
        last_signal_at = datetime(2026, 6, 30, tzinfo=UTC)
        severity = "medium"
        title = "Review Agent run"
        description = "desc"
        suggested_action = "act"
        status = "pending"
        resolution_note = ""
        evidence = [{"source_type": "agent_run", "source_id": "run-1"}]
        created_at = datetime(2026, 6, 30, tzinfo=UTC)

    def fake_get_agent_run(db, run_id):
        called["agent_run_id"] = run_id
        return FakeRun()

    def fake_list_run_suggestions(db, *, run_id):
        called["run_id"] = run_id
        return [Suggestion()]

    monkeypatch.setattr(
        knowledge_operations_api.agent_run_repo,
        "get_agent_run",
        fake_get_agent_run,
    )
    monkeypatch.setattr(
        knowledge_operations_service,
        "list_run_suggestions",
        fake_list_run_suggestions,
    )

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get("/knowledge-operations/suggestions", params={"run_id": "run-1"})
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert called == {"agent_run_id": "run-1", "run_id": "run-1"}
    assert response.json()["suggestions"][0]["item_id"] == "item-1"
