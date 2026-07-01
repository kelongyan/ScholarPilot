"""Integration tests for the document upload API.

The upload endpoint saves a source document and enqueues an async job. We mock the
queue (no Redis) and DB session (no PostgreSQL) to test the HTTP contract.
"""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app

client = TestClient(app)


def _fake_pdf_bytes() -> bytes:
    """Return minimal valid PDF bytes."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Test paper content.")
    buf = BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


class _FakeDB:
    """In-memory DB session that captures created objects."""

    def __init__(self) -> None:
        self.added: list = []

    def add(self, obj) -> None:
        self.added.append(obj)

    def commit(self) -> None:
        from datetime import datetime

        for obj in self.added:
            # Emulate DB server defaults that real commit/refresh would populate.
            if not getattr(obj, "id", None):
                object.__setattr__(obj, "id", "fake-id")
            if getattr(obj, "page_count", None) is None:
                object.__setattr__(obj, "page_count", 0)
            if getattr(obj, "error_message", None) is None:
                object.__setattr__(obj, "error_message", "")
            if getattr(obj, "created_at", None) is None:
                object.__setattr__(obj, "created_at", datetime.now(UTC))
            if getattr(obj, "updated_at", None) is None:
                object.__setattr__(obj, "updated_at", datetime.now(UTC))

    def refresh(self, obj) -> None:
        pass

    def close(self) -> None:
        pass


class _FakeDocument:
    doc_id = "doc-1"
    knowledge_base_id = "kb-1"
    title = "Runbook"
    source = "text"
    content_hash = "hash-1"
    version = 1
    lifecycle_status = "active"
    replaces_doc_id = ""
    replaced_by_doc_id = ""
    status = "indexed"
    page_count = 1
    error_message = ""
    created_at = datetime.now(UTC)
    updated_at = datetime.now(UTC)


def test_upload_rejects_unsupported_file() -> None:
    """``POST /documents/upload`` rejects unsupported source files."""
    response = client.post(
        "/documents/upload",
        files={"file": ("not_supported.exe", BytesIO(b"hello"), "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_creates_document_and_enqueues(monkeypatch, tmp_path) -> None:
    """Upload saves the file, creates a Document, and enqueues processing."""
    from app.core import config as config_module
    from app.services import document_service

    # Redirect storage to a temp dir.
    settings = config_module.get_settings()
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))

    # Inject a fake DB session via FastAPI dependency override.
    fake_db = _FakeDB()

    def _fake_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _fake_get_db

    # Mock the queue so no Redis is needed.
    class FakeQueue:
        def __init__(self) -> None:
            self.enqueued: list = []

        def enqueue(self, *args, **kwargs):
            self.enqueued.append(args)
            return None

    fake_queue = FakeQueue()
    monkeypatch.setattr(document_service, "get_queue", lambda: fake_queue)

    class FakeKnowledgeBase:
        knowledge_base_id = "kb-default"

    monkeypatch.setattr(
        document_service.knowledge_base_repo,
        "get_or_create_default_knowledge_base",
        lambda db: FakeKnowledgeBase(),
    )

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("paper.pdf", BytesIO(_fake_pdf_bytes()), "application/pdf")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "uploaded"
    assert body["title"] == "paper"
    assert body["source"] == "pdf"
    assert body["doc_id"]
    assert body["knowledge_base_id"] == "kb-default"
    assert len(fake_db.added) == 2
    assert fake_db.added[1].action == "document.uploaded"
    assert fake_db.added[1].resource_id == body["doc_id"]
    assert len(fake_queue.enqueued) == 1


def test_upload_accepts_text_document(monkeypatch, tmp_path) -> None:
    from app.core import config as config_module
    from app.services import document_service

    settings = config_module.get_settings()
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))

    fake_db = _FakeDB()

    def _fake_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _fake_get_db

    class FakeQueue:
        def __init__(self) -> None:
            self.enqueued: list = []

        def enqueue(self, *args, **kwargs):
            self.enqueued.append(args)
            return None

    fake_queue = FakeQueue()
    monkeypatch.setattr(document_service, "get_queue", lambda: fake_queue)

    class FakeKnowledgeBase:
        knowledge_base_id = "kb-default"

    monkeypatch.setattr(
        document_service.knowledge_base_repo,
        "get_or_create_default_knowledge_base",
        lambda db: FakeKnowledgeBase(),
    )

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("runbook.txt", BytesIO(b"triage steps"), "text/plain")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "uploaded"
    assert body["title"] == "runbook"
    assert body["source"] == "text"
    assert body["knowledge_base_id"] == "kb-default"
    assert len(fake_queue.enqueued) == 1


def test_upload_uses_supplied_knowledge_base(monkeypatch, tmp_path) -> None:
    from app.core import config as config_module
    from app.services import document_service

    settings = config_module.get_settings()
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))

    fake_db = _FakeDB()

    def _fake_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _fake_get_db

    class FakeQueue:
        def __init__(self) -> None:
            self.enqueued: list = []

        def enqueue(self, *args, **kwargs):
            self.enqueued.append(args)
            return None

    fake_queue = FakeQueue()
    monkeypatch.setattr(document_service, "get_queue", lambda: fake_queue)

    class FakeKnowledgeBase:
        knowledge_base_id = "kb-123"

    monkeypatch.setattr(
        document_service.knowledge_base_repo,
        "get_knowledge_base",
        lambda db, knowledge_base_id: FakeKnowledgeBase()
        if knowledge_base_id == "kb-123"
        else None,
    )

    try:
        response = client.post(
            "/documents/upload",
            data={"knowledge_base_id": "kb-123"},
            files={"file": ("paper.pdf", BytesIO(_fake_pdf_bytes()), "application/pdf")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["knowledge_base_id"] == "kb-123"
    assert len(fake_queue.enqueued) == 1
    assert len(fake_db.added) == 2
    assert fake_db.added[1].knowledge_base_id == "kb-123"


def test_replace_document_creates_new_version(monkeypatch) -> None:
    from app.services import document_service

    class ReplacementDocument(_FakeDocument):
        doc_id = "doc-2"
        version = 2
        replaces_doc_id = "doc-1"

    captured = {}
    monkeypatch.setattr(document_service, "get_document", lambda db, doc_id: _FakeDocument())
    monkeypatch.setattr(
        document_service,
        "replace_document",
        lambda db, doc_id, file: (
            captured.setdefault("doc_id", doc_id),
            ReplacementDocument(),
        )[1],
    )

    fake_db = _FakeDB()

    def _fake_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.post(
            "/documents/doc-1/replace",
            files={"file": ("replacement.txt", BytesIO(b"new text"), "text/plain")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["doc_id"] == "doc-2"
    assert body["version"] == 2
    assert body["replaces_doc_id"] == "doc-1"
    assert captured["doc_id"] == "doc-1"


def test_archive_document_sets_lifecycle_status(monkeypatch) -> None:
    from app.services import document_service

    class ArchivedDocument(_FakeDocument):
        lifecycle_status = "archived"

    monkeypatch.setattr(document_service, "get_document", lambda db, doc_id: _FakeDocument())
    monkeypatch.setattr(
        document_service,
        "archive_document",
        lambda db, doc_id: ArchivedDocument(),
    )

    fake_db = _FakeDB()

    def _fake_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.post("/documents/doc-1/archive")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["lifecycle_status"] == "archived"
