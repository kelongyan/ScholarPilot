"""Integration tests for the document upload API.

The upload endpoint saves the PDF and enqueues an async job. We mock the
queue (no Redis) and DB session (no PostgreSQL) to test the HTTP contract.
"""

from __future__ import annotations

from datetime import UTC
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


def test_upload_rejects_non_pdf() -> None:
    """``POST /documents/upload`` rejects non-PDF files."""
    response = client.post(
        "/documents/upload",
        files={"file": ("not_a_pdf.txt", BytesIO(b"hello"), "text/plain")},
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
    assert len(fake_db.added) == 1
    assert len(fake_queue.enqueued) == 1
