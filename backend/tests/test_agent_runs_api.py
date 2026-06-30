"""Tests for controlled Agent workflow API routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app
from app.services.agent_service import AgentRunResult, AgentStepResult

client = TestClient(app)


def _fake_get_db():
    yield object()


def _setup_db_override() -> None:
    app.dependency_overrides[get_db] = _fake_get_db


def _teardown_db_override() -> None:
    app.dependency_overrides.pop(get_db, None)


def _agent_result() -> AgentRunResult:
    return AgentRunResult(
        run_id="run-1",
        route="short",
        status="completed",
        doc_id="doc-1",
        knowledge_base_id=None,
        question="What changed?",
        answer="A controlled Agent run completed.",
        answer_status="answered",
        citations=[],
        trace=None,
        agent_steps=[
            AgentStepResult(
                sequence=1,
                agent_name="planner_agent",
                status="completed",
                output_json={"route": "short"},
            )
        ],
        total_latency_ms=7,
    )


def test_run_agent_endpoint_returns_step_trace(monkeypatch) -> None:
    from app.repositories import document_repo
    from app.services import agent_service

    class FakeDoc:
        status = "indexed"

    monkeypatch.setattr(document_repo, "get_document", lambda db, doc_id: FakeDoc())
    monkeypatch.setattr(
        agent_service,
        "run_agent_workflow",
        lambda **kwargs: _agent_result(),
    )
    monkeypatch.setattr(
        agent_service,
        "create_agent_run",
        lambda *args, **kwargs: None,
    )

    _setup_db_override()
    try:
        response = client.post(
            "/agent-runs",
            json={"doc_id": "doc-1", "question": "What changed?"},
        )
    finally:
        _teardown_db_override()

    assert response.status_code == 201
    body = response.json()
    assert body["run_id"] == "run-1"
    assert body["route"] == "short"
    assert body["agent_steps"][0]["agent_name"] == "planner_agent"


def test_run_agent_rejects_non_indexed_document(monkeypatch) -> None:
    from app.repositories import document_repo

    class FakeDoc:
        status = "indexing"

    monkeypatch.setattr(document_repo, "get_document", lambda db, doc_id: FakeDoc())

    _setup_db_override()
    try:
        response = client.post(
            "/agent-runs",
            json={"doc_id": "doc-1", "question": "What changed?"},
        )
    finally:
        _teardown_db_override()

    assert response.status_code == 409


def test_get_agent_run_404(monkeypatch) -> None:
    from app.services import agent_service

    monkeypatch.setattr(agent_service, "get_agent_run_response", lambda db, run_id: None)

    _setup_db_override()
    try:
        response = client.get("/agent-runs/missing")
    finally:
        _teardown_db_override()

    assert response.status_code == 404
