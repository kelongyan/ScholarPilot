"""Document and chunk schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """Public representation of a document."""

    model_config = ConfigDict(from_attributes=True)

    doc_id: str
    title: str
    source: str
    status: str
    page_count: int
    error_message: str = ""
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """A paginated-style list of documents (Phase 1: no pagination)."""

    documents: list[DocumentResponse]


class ChunkResponse(BaseModel):
    """Public representation of a chunk."""

    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    doc_id: str
    section: str
    page_start: int
    page_end: int
    text: str
    chunk_type: str
    token_count: int
    chunk_index: int
