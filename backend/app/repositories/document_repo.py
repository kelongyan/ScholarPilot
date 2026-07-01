"""Document repository: data access for documents and chunks.

Per RULE.md §12.3, repositories only handle data read/write — no LLM calls,
no external APIs, no business decisions.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Chunk, Document

DELETED_LIFECYCLE_STATUS = "deleted"


def create_document(db: Session, document: Document) -> Document:
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_document(db: Session, doc_id: str) -> Document | None:
    return db.scalar(select(Document).where(Document.doc_id == doc_id))


def get_document_by_id(db: Session, pk: str) -> Document | None:
    return db.get(Document, pk)


def list_documents(db: Session) -> list[Document]:
    return list(
        db.scalars(
            select(Document)
            .where(Document.lifecycle_status != DELETED_LIFECYCLE_STATUS)
            .order_by(Document.created_at.desc())
        )
    )


def list_documents_by_knowledge_base(
    db: Session,
    knowledge_base_id: str,
) -> list[Document]:
    return list(
        db.scalars(
            select(Document)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .where(Document.lifecycle_status != DELETED_LIFECYCLE_STATUS)
            .order_by(Document.created_at.desc())
        )
    )


def list_active_documents_by_knowledge_base(
    db: Session,
    knowledge_base_id: str,
) -> list[Document]:
    return list(
        db.scalars(
            select(Document)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .where(Document.lifecycle_status == "active")
            .order_by(Document.created_at.desc())
        )
    )


def update_lifecycle(
    db: Session,
    doc_id: str,
    lifecycle_status: str,
    *,
    replaced_by_doc_id: str | None = None,
) -> Document | None:
    doc = get_document(db, doc_id)
    if doc is None:
        return None
    doc.lifecycle_status = lifecycle_status
    if replaced_by_doc_id is not None:
        doc.replaced_by_doc_id = replaced_by_doc_id
    db.commit()
    db.refresh(doc)
    return doc


def update_status(
    db: Session,
    doc_id: str,
    status: str,
    *,
    error_message: str = "",
    page_count: int | None = None,
) -> Document | None:
    doc = get_document(db, doc_id)
    if doc is None:
        return None
    doc.status = status
    if error_message:
        doc.error_message = error_message
    if page_count is not None:
        doc.page_count = page_count
    db.commit()
    db.refresh(doc)
    return doc


def delete_document_chunks(db: Session, doc_id: str) -> None:
    db.query(Chunk).filter(Chunk.doc_id == doc_id).delete(
        synchronize_session=False
    )
    db.commit()


def create_chunks(db: Session, chunks: list[Chunk]) -> None:
    db.add_all(chunks)
    db.commit()


def list_chunks(db: Session, doc_id: str) -> list[Chunk]:
    return list(
        db.scalars(
            select(Chunk).where(Chunk.doc_id == doc_id).order_by(Chunk.chunk_index)
        )
    )


def list_chunks_by_doc_ids(db: Session, doc_ids: list[str]) -> list[Chunk]:
    if not doc_ids:
        return []
    return list(
        db.scalars(
            select(Chunk)
            .where(Chunk.doc_id.in_(doc_ids))
            .order_by(Chunk.doc_id, Chunk.chunk_index)
        )
    )
