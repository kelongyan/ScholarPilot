"""Citation ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Citation(Base):
    """A citation linking an answer to a source chunk.

    Persisted so answers remain traceable after generation.
    """

    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    citation_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=_uuid)
    chunk_id: Mapped[str] = mapped_column(String(128), ForeignKey("chunks.chunk_id"), index=True)
    doc_id: Mapped[str] = mapped_column(String(128), index=True)
    quote: Mapped[str] = mapped_column(Text, default="")
    page: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
