"""Tests for minimal auth and RBAC boundaries."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.db import get_db
from app.main import app

client = TestClient(app)


class _FakeKnowledgeBase:
    def __init__(self, knowledge_base_id: str, name: str) -> None:
        self.knowledge_base_id = knowledge_base_id
        self.name = name
        self.description = ""
        self.status = "active"
        self.owner_id = "owner-1"
        self.visibility = "private"
        self.created_at = "2026-06-30T00:00:00"
        self.updated_at = "2026-06-30T00:00:00"


def _fake_get_db():
    yield object()


def _mock_no_configured_memberships(monkeypatch) -> None:
    from app.services import governance_service

    monkeypatch.setattr(
        governance_service.governance_repo,
        "get_member",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(
        governance_service.governance_repo,
        "has_memberships",
        lambda db, **kwargs: False,
    )


def test_auth_me_returns_dev_admin_when_auth_disabled(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "auth_enabled", False)
    monkeypatch.setattr(settings, "auth_dev_actor_id", "dev-actor")

    response = client.get("/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["actor_id"] == "dev-actor"
    assert body["role"] == "admin"
    assert body["auth_enabled"] is False


def test_auth_enabled_requires_bearer_token(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_admin_token", "admin-token")

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_user_token_cannot_read_audit_logs(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_user_token", "user-token")
    monkeypatch.setattr(settings, "auth_admin_token", "admin-token")

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/audit-logs",
            headers={"Authorization": "Bearer user-token"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 403


def test_admin_token_can_read_audit_logs(monkeypatch) -> None:
    from app.services import audit_log_service

    settings = get_settings()
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_admin_token", "admin-token")
    monkeypatch.setattr(audit_log_service, "list_audit_logs", lambda db, **kwargs: [])

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/audit-logs",
            headers={"Authorization": "Bearer admin-token"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json() == {"audit_logs": []}


def test_jwt_knowledge_base_scope_filters_list(monkeypatch) -> None:
    from app.services import knowledge_base_service

    settings = get_settings()
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_jwt_secret", "test-secret")
    _mock_no_configured_memberships(monkeypatch)
    monkeypatch.setattr(
        knowledge_base_service,
        "list_knowledge_bases",
        lambda db: [
            _FakeKnowledgeBase("kb-allowed", "Allowed"),
            _FakeKnowledgeBase("kb-denied", "Denied"),
        ],
    )
    token = _jwt(
        {
            "sub": "user-1",
            "role": "user",
            "knowledge_base_ids": ["kb-allowed"],
        },
        secret="test-secret",
    )

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/knowledge-bases",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    body = response.json()
    assert [kb["knowledge_base_id"] for kb in body["knowledge_bases"]] == ["kb-allowed"]


def test_kb_manager_jwt_can_read_scoped_observability(monkeypatch) -> None:
    from app.schemas.observability import ObservabilitySummaryResponse
    from app.services import observability_service

    settings = get_settings()
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_jwt_secret", "test-secret")
    _mock_no_configured_memberships(monkeypatch)
    captured = {}

    def fake_get_summary(db, **kwargs):
        captured.update(kwargs)
        return ObservabilitySummaryResponse(
            knowledge_base_id="kb-allowed",
            generated_at="2026-07-01T00:00:00Z",
        )

    monkeypatch.setattr(observability_service, "get_summary", fake_get_summary)
    token = _jwt(
        {
            "sub": "manager-1",
            "role": "kb_manager",
            "knowledge_base_ids": ["kb-allowed"],
        },
        secret="test-secret",
    )

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/observability/summary",
            params={"knowledge_base_id": "kb-allowed"},
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert captured["knowledge_base_id"] == "kb-allowed"


def test_kb_manager_jwt_cannot_read_denied_chat_trace(monkeypatch) -> None:
    from app.services import chat_trace_service, question_log_service

    settings = get_settings()
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_jwt_secret", "test-secret")
    _mock_no_configured_memberships(monkeypatch)

    class FakeTrace:
        question_log_id = "ql-denied"

    class FakeQuestionLog:
        knowledge_base_id = "kb-denied"

    monkeypatch.setattr(
        chat_trace_service,
        "get_chat_trace",
        lambda db, trace_id: FakeTrace(),
    )
    monkeypatch.setattr(
        question_log_service,
        "get_question_log",
        lambda db, question_log_id: FakeQuestionLog(),
    )
    token = _jwt(
        {
            "sub": "manager-1",
            "role": "kb_manager",
            "knowledge_base_ids": ["kb-allowed"],
        },
        secret="test-secret",
    )

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/chat-traces/trace-denied",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 403


def _jwt(claims: dict[str, object], *, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _base64url_json(header)
    encoded_claims = _base64url_json(claims)
    signing_input = f"{encoded_header}.{encoded_claims}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_claims}.{_base64url(signature)}"


def _base64url_json(payload: dict[str, object]) -> str:
    return _base64url(json.dumps(payload, separators=(",", ":")).encode())


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")
