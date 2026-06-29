"""Document service: upload handling and status management.

Uploads save the PDF to the local storage directory, create a Document
record, and enqueue an async processing job. The heavy lifting (parse, chunk,
embed, index) lives in the RQ worker (``app.workers.tasks``).
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis import get_queue
from app.models import Document
from app.repositories import document_repo

settings = get_settings()


def _storage_path() -> Path:
    path = Path(settings.storage_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def upload_pdf(db: Session, file: UploadFile) -> Document:
    """Save an uploaded PDF and enqueue async processing.

    Args:
        db: Database session.
        file: The uploaded file.

    Returns:
        The created :class:`Document` (status ``uploaded``).
    """
    storage = _storage_path()
    doc_id = str(uuid.uuid4())
    # Keep the original filename for display; prefix with doc_id for uniqueness.
    safe_name = Path(file.filename or "document.pdf").name
    file_name = f"{doc_id}_{safe_name}"
    file_path = storage / file_name

    with file_path.open("wb") as f:
        f.write(file.file.read())

    title = Path(safe_name).stem
    document = Document(
        doc_id=doc_id,
        title=title,
        source="pdf",
        file_path=str(file_path),
        status="uploaded",
    )
    document = document_repo.create_document(db, document)

    # Enqueue async processing.
    queue = get_queue()
    queue.enqueue("app.workers.tasks.process_document", doc_id)

    return document


def get_document(db: Session, doc_id: str) -> Document | None:
    return document_repo.get_document(db, doc_id)


def list_documents(db: Session) -> list[Document]:
    return document_repo.list_documents(db)


def reindex_document(db: Session, doc_id: str) -> Document | None:
    """Re-enqueue processing for an existing document."""
    doc = document_repo.get_document(db, doc_id)
    if doc is None:
        return None
    document_repo.update_status(db, doc_id, "uploaded")
    queue = get_queue()
    queue.enqueue("app.workers.tasks.process_document", doc_id)
    return document_repo.get_document(db, doc_id)
