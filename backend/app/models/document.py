"""Document and Chunk ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase


def _uuid() -> str:
    return str(uuid.uuid4())


class Document(Base):
    """A source document (e.g. an uploaded PDF)."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    doc_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    knowledge_base_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("knowledge_bases.knowledge_base_id", ondelete="RESTRICT"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), default="")
    source: Mapped[str] = mapped_column(String(32), default="pdf")
    file_path: Mapped[str] = mapped_column(String(1024), default="")
    content_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    lifecycle_status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    replaces_doc_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    replaced_by_doc_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    # uploaded | parsing | parsed | indexing | indexed | failed
    status: Mapped[str] = mapped_column(String(32), default="uploaded", index=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    chunks: Mapped[list[Chunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    knowledge_base: Mapped[KnowledgeBase] = relationship(back_populates="documents")


class Chunk(Base):
    """A text chunk extracted from a document, with source provenance."""

    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    chunk_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    doc_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("documents.doc_id", ondelete="CASCADE"), index=True
    )
    section: Mapped[str] = mapped_column(String(256), default="")
    page_start: Mapped[int] = mapped_column(Integer, default=0)
    page_end: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text, default="")
    # paragraph | table | figure_caption | reference
    chunk_type: Mapped[str] = mapped_column(String(32), default="paragraph")
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="chunks")
