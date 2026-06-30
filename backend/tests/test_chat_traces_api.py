"""Tests for persisted chat trace API routes."""

from __future__ import annotations

from datetime import UTC

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app

client = TestClient(app)


class _FakeDB:
    def add(self, obj) -> None:
        self.obj = obj

    def commit(self) -> None:
        from datetime import datetime

        obj = getattr(self, "obj", None)
        if obj is None:
            return
        if not getattr(obj, "id", None):
            object.__setattr__(obj, "id", "fake-id")
        if getattr(obj, "created_at", None) is None:
            object.__setattr__(obj, "created_at", datetime.now(UTC))
        if getattr(obj, "updated_at", None) is None:
            object.__setattr__(obj, "updated_at", datetime.now(UTC))

    def refresh(self, obj) -> None:
        pass

    def scalar(self, query):
        return None

    def scalars(self, query):
        return iter([])

    def close(self) -> None:
        pass


def _override_db(fake_db: _FakeDB) -> None:
    def _fake_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _fake_get_db


def _clear_override() -> None:
    app.dependency_overrides.pop(get_db, None)


def test_list_chat_traces(monkeypatch) -> None:
    from app.services import chat_trace_service

    class FakeTrace:
        trace_id = "trace-1"
        question_log_id = "ql-1"
        query = "What is indexed?"
        rewritten_query = "indexed?"
        dense_results_json = []
        sparse_results_json = []
        fused_results_json = []
        reranked_results_json = []
        evidence_pack_json = []
        answer = "The document is indexed."
        citations_json = []
        answer_status = "answered"
        model = ""
        latency_ms = 12
        created_at = "2026-06-30T00:00:00Z"
        updated_at = "2026-06-30T00:00:00Z"

    monkeypatch.setattr(chat_trace_service, "list_chat_traces", lambda db: [FakeTrace()])
    fake_db = _FakeDB()
    _override_db(fake_db)

    try:
        response = client.get("/chat-traces")
    finally:
        _clear_override()

    assert response.status_code == 200
    assert response.json()["chat_traces"][0]["trace_id"] == "trace-1"


def test_get_chat_trace_404(monkeypatch) -> None:
    from app.services import chat_trace_service

    monkeypatch.setattr(chat_trace_service, "get_chat_trace", lambda db, trace_id: None)
    fake_db = _FakeDB()
    _override_db(fake_db)

    try:
        response = client.get("/chat-traces/missing")
    finally:
        _clear_override()

    assert response.status_code == 404
