"""Tests for knowledge base API routes."""

from __future__ import annotations

from datetime import UTC

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app

client = TestClient(app)


class _FakeDB:
    def __init__(self) -> None:
        self.items: list = []

    def add(self, obj) -> None:
        self.items.append(obj)

    def commit(self) -> None:
        from datetime import datetime

        for obj in self.items:
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

    def close(self) -> None:
        pass


def _override_db(fake_db: _FakeDB) -> None:
    def _fake_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _fake_get_db


def _clear_override() -> None:
    app.dependency_overrides.pop(get_db, None)


def test_create_and_list_knowledge_bases(monkeypatch) -> None:
    fake_db = _FakeDB()
    _override_db(fake_db)

    try:
        response = client.post(
            "/knowledge-bases",
            json={
                "name": "Engineering",
                "description": "Team docs",
                "status": "active",
                "owner_id": "owner-1",
                "visibility": "private",
            },
        )
    finally:
        _clear_override()

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Engineering"
    assert body["knowledge_base_id"]


def test_get_knowledge_base_404(monkeypatch) -> None:
    from app.repositories import knowledge_base_repo

    monkeypatch.setattr(knowledge_base_repo, "get_knowledge_base", lambda db, kb: None)
    fake_db = _FakeDB()
    _override_db(fake_db)

    try:
        response = client.get("/knowledge-bases/missing")
    finally:
        _clear_override()

    assert response.status_code == 404


def test_list_documents_filters_by_knowledge_base(monkeypatch) -> None:
    from app.repositories import knowledge_base_repo
    from app.services import document_service

    class FakeKB:
        knowledge_base_id = "kb-123"

    monkeypatch.setattr(
        knowledge_base_repo, "get_knowledge_base", lambda db, kb: FakeKB()
    )
    monkeypatch.setattr(
        document_service,
        "list_documents_by_knowledge_base",
        lambda db, kb: [],
    )

    fake_db = _FakeDB()
    _override_db(fake_db)

    try:
        response = client.get("/documents", params={"knowledge_base_id": "kb-123"})
    finally:
        _clear_override()

    assert response.status_code == 200
    assert response.json() == {"documents": []}
