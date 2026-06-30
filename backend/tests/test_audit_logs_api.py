"""Tests for audit log API routes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app

client = TestClient(app)


class _FakeAuditLog:
    audit_id = "audit-1"
    actor_id = "system"
    action = "document.uploaded"
    resource_type = "document"
    resource_id = "doc-1"
    knowledge_base_id = "kb-1"
    detail_json = {"title": "Handbook"}
    created_at = datetime(2026, 6, 30, tzinfo=UTC)


def _fake_get_db():
    yield object()


def test_list_audit_logs(monkeypatch) -> None:
    from app.services import audit_log_service

    captured = {}

    def fake_list_audit_logs(db, **kwargs):
        captured.update(kwargs)
        return [_FakeAuditLog()]

    monkeypatch.setattr(audit_log_service, "list_audit_logs", fake_list_audit_logs)

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/audit-logs",
            params={
                "knowledge_base_id": "kb-1",
                "action": "document.uploaded",
                "resource_type": "document",
                "resource_id": "doc-1",
                "actor_id": "system",
                "created_from": "2026-06-01T00:00:00",
                "created_to": "2026-06-30T23:59:59",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    body = response.json()
    assert body["audit_logs"][0]["audit_id"] == "audit-1"
    assert body["audit_logs"][0]["action"] == "document.uploaded"
    assert body["audit_logs"][0]["detail_json"] == {"title": "Handbook"}
    assert captured["knowledge_base_id"] == "kb-1"
    assert captured["action"] == "document.uploaded"
    assert captured["resource_type"] == "document"
    assert captured["resource_id"] == "doc-1"
    assert captured["actor_id"] == "system"
    assert captured["created_from"].isoformat() == "2026-06-01T00:00:00"
    assert captured["created_to"].isoformat() == "2026-06-30T23:59:59"
