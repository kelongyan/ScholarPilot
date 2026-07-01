"""Document service: upload handling and status management.

Uploads save a supported source document to the local storage directory, create
a Document record, and enqueue an async processing job. The heavy lifting
(parse, chunk, embed, index) lives in the RQ worker (``app.workers.tasks``).
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis import get_queue
from app.models import Document
from app.repositories import document_repo, knowledge_base_repo
from app.services.parser_service import get_supported_document_source
from app.services.vector_service import delete_document_vectors

settings = get_settings()

ACTIVE_LIFECYCLE_STATUS = "active"
ARCHIVED_LIFECYCLE_STATUS = "archived"
DELETED_LIFECYCLE_STATUS = "deleted"


def _storage_path() -> Path:
    path = Path(settings.storage_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def upload_document(
    db: Session,
    file: UploadFile,
    *,
    knowledge_base_id: str | None = None,
    replaces_doc_id: str = "",
    version: int = 1,
) -> Document:
    """Save an uploaded source document and enqueue async processing.

    Args:
        db: Database session.
        file: The uploaded file.

    Returns:
        The created :class:`Document` (status ``uploaded``).
    """
    knowledge_base = (
        knowledge_base_repo.get_knowledge_base(db, knowledge_base_id)
        if knowledge_base_id
        else knowledge_base_repo.get_or_create_default_knowledge_base(db)
    )
    if knowledge_base is None:
        raise ValueError("knowledge base not found")

    safe_name = Path(file.filename or "document").name
    source = get_supported_document_source(safe_name)
    if source is None:
        raise ValueError("unsupported document type")

    storage = _storage_path()
    doc_id = str(uuid.uuid4())
    # Keep the original filename for display; prefix with doc_id for uniqueness.
    file_name = f"{doc_id}_{safe_name}"
    file_path = storage / file_name

    content = file.file.read()
    with file_path.open("wb") as f:
        f.write(content)

    title = Path(safe_name).stem
    content_hash = hashlib.sha256(content).hexdigest()

    # Store a POSIX-style relative path so both the Windows API server and the
    # Linux RQ worker can resolve it against the backend root. Absolute paths
    # with OS-specific separators break when API and worker run on different
    # operating systems sharing one database.
    relative_path = f"{settings.storage_dir}/{file_name}"
    document = Document(
        doc_id=doc_id,
        knowledge_base_id=knowledge_base.knowledge_base_id,
        title=title,
        source=source,
        file_path=relative_path,
        content_hash=content_hash,
        version=version,
        lifecycle_status=ACTIVE_LIFECYCLE_STATUS,
        replaces_doc_id=replaces_doc_id,
        replaced_by_doc_id="",
        status="uploaded",
    )
    document = document_repo.create_document(db, document)

    # Enqueue async processing.
    queue = get_queue()
    queue.enqueue("app.workers.tasks.process_document", doc_id)

    return document


def upload_pdf(
    db: Session,
    file: UploadFile,
    *,
    knowledge_base_id: str | None = None,
) -> Document:
    """Backward-compatible wrapper for older PDF upload call sites."""
    return upload_document(db, file, knowledge_base_id=knowledge_base_id)


def replace_document(db: Session, doc_id: str, file: UploadFile) -> Document | None:
    """Upload a new active version and archive the replaced document."""
    existing = document_repo.get_document(db, doc_id)
    if existing is None or existing.lifecycle_status == DELETED_LIFECYCLE_STATUS:
        return None
    if existing.lifecycle_status != ACTIVE_LIFECYCLE_STATUS:
        raise ValueError("Only active documents can be replaced")

    replacement = upload_document(
        db,
        file,
        knowledge_base_id=existing.knowledge_base_id,
        replaces_doc_id=existing.doc_id,
        version=getattr(existing, "version", 1) + 1,
    )
    archive_document(db, existing.doc_id, replaced_by_doc_id=replacement.doc_id)
    return replacement


def get_document(db: Session, doc_id: str) -> Document | None:
    return document_repo.get_document(db, doc_id)


def list_documents(db: Session) -> list[Document]:
    return document_repo.list_documents(db)


def list_documents_by_knowledge_base(
    db: Session,
    knowledge_base_id: str,
) -> list[Document]:
    return document_repo.list_documents_by_knowledge_base(db, knowledge_base_id)


def reindex_document(db: Session, doc_id: str) -> Document | None:
    """Re-enqueue processing for an existing document."""
    doc = document_repo.get_document(db, doc_id)
    if doc is None:
        return None
    if doc.lifecycle_status != ACTIVE_LIFECYCLE_STATUS:
        raise ValueError("Only active documents can be reindexed")
    document_repo.update_status(db, doc_id, "uploaded")
    queue = get_queue()
    queue.enqueue("app.workers.tasks.process_document", doc_id)
    return document_repo.get_document(db, doc_id)


def archive_document(
    db: Session,
    doc_id: str,
    *,
    replaced_by_doc_id: str = "",
) -> Document | None:
    """Archive a document and remove it from retrieval indexes."""
    doc = document_repo.update_lifecycle(
        db,
        doc_id,
        ARCHIVED_LIFECYCLE_STATUS,
        replaced_by_doc_id=replaced_by_doc_id,
    )
    if doc is None:
        return None
    _retire_document_index(db, doc_id)
    return doc


def restore_document(db: Session, doc_id: str) -> Document | None:
    """Restore an archived document and queue reindexing."""
    existing = document_repo.get_document(db, doc_id)
    if existing is None or existing.lifecycle_status == DELETED_LIFECYCLE_STATUS:
        return None
    doc = document_repo.update_lifecycle(
        db,
        doc_id,
        ACTIVE_LIFECYCLE_STATUS,
        replaced_by_doc_id="",
    )
    if doc is None:
        return None
    document_repo.update_status(db, doc_id, "uploaded")
    queue = get_queue()
    queue.enqueue("app.workers.tasks.process_document", doc_id)
    return document_repo.get_document(db, doc_id)


def delete_document(db: Session, doc_id: str) -> Document | None:
    """Soft-delete a document and remove its indexed chunks/vectors."""
    doc = document_repo.update_lifecycle(db, doc_id, DELETED_LIFECYCLE_STATUS)
    if doc is None:
        return None
    _retire_document_index(db, doc_id)
    return doc


def is_active_document(document: Document) -> bool:
    return document.lifecycle_status == ACTIVE_LIFECYCLE_STATUS


def _retire_document_index(db: Session, doc_id: str) -> None:
    delete_document_vectors(doc_id)
    document_repo.delete_document_chunks(db, doc_id)
