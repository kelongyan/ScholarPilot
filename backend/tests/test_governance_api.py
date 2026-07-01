"""Tests for governance API routes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app

client = TestClient(app)


def _fake_get_db():
    yield object()


class _FakeUser:
    user_id = "system"
    email = ""
    display_name = "system"
    status = "active"
    role = "admin"
    created_at = datetime(2026, 7, 1, tzinfo=UTC)
    updated_at = datetime(2026, 7, 1, tzinfo=UTC)


class _FakeMember:
    membership_id = "member-1"
    knowledge_base_id = "kb-1"
    user_id = "user-1"
    role = "manager"
    status = "active"
    created_by = "system"
    created_at = datetime(2026, 7, 1, tzinfo=UTC)
    updated_at = datetime(2026, 7, 1, tzinfo=UTC)


def test_get_current_governance_user(monkeypatch) -> None:
    from app.services import governance_service

    monkeypatch.setattr(
        governance_service,
        "ensure_current_user_account",
        lambda db, current_user: _FakeUser(),
    )

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get("/governance/users/me")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["user_id"] == "system"


def test_upsert_knowledge_base_member(monkeypatch) -> None:
    from app.repositories import knowledge_base_repo
    from app.services import audit_log_service, governance_service

    class FakeKnowledgeBase:
        knowledge_base_id = "kb-1"

    captured = {}

    def fake_can_access(db, current_user, knowledge_base_id, *, min_member_role="viewer"):
        captured["min_member_role"] = min_member_role
        return True

    monkeypatch.setattr(
        knowledge_base_repo,
        "get_knowledge_base",
        lambda db, knowledge_base_id: FakeKnowledgeBase(),
    )
    monkeypatch.setattr(
        governance_service,
        "can_access_knowledge_base",
        fake_can_access,
    )
    monkeypatch.setattr(
        governance_service,
        "upsert_knowledge_base_member",
        lambda db, **kwargs: captured.setdefault("member", _FakeMember()),
    )
    monkeypatch.setattr(audit_log_service, "try_log_event", lambda db, **kwargs: None)

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.put(
            "/governance/knowledge-bases/kb-1/members/user-1",
            json={"role": "manager", "status": "active"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["membership_id"] == "member-1"
    assert captured["member"].role == "manager"
    assert captured["min_member_role"] == "owner"
