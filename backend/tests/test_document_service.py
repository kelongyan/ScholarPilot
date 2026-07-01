"""Tests for document lifecycle service behavior."""

from __future__ import annotations

from types import SimpleNamespace

from app.services import document_service


def test_archive_document_retires_chunks_and_vectors(monkeypatch) -> None:
    doc = SimpleNamespace(doc_id="doc-1", lifecycle_status="archived")
    captured = {}

    monkeypatch.setattr(
        document_service.document_repo,
        "update_lifecycle",
        lambda db, doc_id, lifecycle_status, **kwargs: (
            captured.setdefault("lifecycle", (doc_id, lifecycle_status, kwargs)),
            doc,
        )[1],
    )
    monkeypatch.setattr(
        document_service,
        "delete_document_vectors",
        lambda doc_id: captured.setdefault("vectors", doc_id),
    )
    monkeypatch.setattr(
        document_service.document_repo,
        "delete_document_chunks",
        lambda db, doc_id: captured.setdefault("chunks", doc_id),
    )

    result = document_service.archive_document(object(), "doc-1", replaced_by_doc_id="doc-2")

    assert result is doc
    assert captured["lifecycle"] == (
        "doc-1",
        "archived",
        {"replaced_by_doc_id": "doc-2"},
    )
    assert captured["vectors"] == "doc-1"
    assert captured["chunks"] == "doc-1"


def test_delete_document_retires_chunks_and_vectors(monkeypatch) -> None:
    doc = SimpleNamespace(doc_id="doc-1", lifecycle_status="deleted")
    captured = {}

    monkeypatch.setattr(
        document_service.document_repo,
        "update_lifecycle",
        lambda db, doc_id, lifecycle_status, **kwargs: (
            captured.setdefault("lifecycle", (doc_id, lifecycle_status)),
            doc,
        )[1],
    )
    monkeypatch.setattr(
        document_service,
        "delete_document_vectors",
        lambda doc_id: captured.setdefault("vectors", doc_id),
    )
    monkeypatch.setattr(
        document_service.document_repo,
        "delete_document_chunks",
        lambda db, doc_id: captured.setdefault("chunks", doc_id),
    )

    result = document_service.delete_document(object(), "doc-1")

    assert result is doc
    assert captured["lifecycle"] == ("doc-1", "deleted")
    assert captured["vectors"] == "doc-1"
    assert captured["chunks"] == "doc-1"


def test_restore_document_requeues_indexing(monkeypatch) -> None:
    existing = SimpleNamespace(doc_id="doc-1", lifecycle_status="archived")
    restored = SimpleNamespace(doc_id="doc-1", lifecycle_status="active")
    captured = {}

    monkeypatch.setattr(
        document_service.document_repo,
        "get_document",
        lambda db, doc_id: existing if "status" not in captured else restored,
    )
    monkeypatch.setattr(
        document_service.document_repo,
        "update_lifecycle",
        lambda db, doc_id, lifecycle_status, **kwargs: (
            captured.setdefault("lifecycle", (doc_id, lifecycle_status, kwargs)),
            restored,
        )[1],
    )
    monkeypatch.setattr(
        document_service.document_repo,
        "update_status",
        lambda db, doc_id, status: captured.setdefault("status", (doc_id, status)),
    )

    class FakeQueue:
        def enqueue(self, *args):
            captured["enqueue"] = args

    monkeypatch.setattr(document_service, "get_queue", lambda: FakeQueue())

    result = document_service.restore_document(object(), "doc-1")

    assert result is restored
    assert captured["lifecycle"] == (
        "doc-1",
        "active",
        {"replaced_by_doc_id": ""},
    )
    assert captured["status"] == ("doc-1", "uploaded")
    assert captured["enqueue"] == ("app.workers.tasks.process_document", "doc-1")


def test_replace_document_creates_next_version_and_archives_old(monkeypatch) -> None:
    existing = SimpleNamespace(
        doc_id="doc-1",
        knowledge_base_id="kb-1",
        lifecycle_status="active",
        version=3,
    )
    replacement = SimpleNamespace(doc_id="doc-2", version=4)
    captured = {}

    monkeypatch.setattr(
        document_service.document_repo,
        "get_document",
        lambda db, doc_id: existing,
    )
    monkeypatch.setattr(
        document_service,
        "upload_document",
        lambda db, file, **kwargs: (
            captured.setdefault("upload", kwargs),
            replacement,
        )[1],
    )
    monkeypatch.setattr(
        document_service,
        "archive_document",
        lambda db, doc_id, **kwargs: captured.setdefault("archive", (doc_id, kwargs)),
    )

    result = document_service.replace_document(object(), "doc-1", object())

    assert result is replacement
    assert captured["upload"] == {
        "knowledge_base_id": "kb-1",
        "replaces_doc_id": "doc-1",
        "version": 4,
    }
    assert captured["archive"] == ("doc-1", {"replaced_by_doc_id": "doc-2"})
