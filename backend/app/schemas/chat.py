"""Chat request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """A question about a single document."""

    doc_id: str = Field(..., description="The document to query against.")
    question: str = Field(..., min_length=1, description="The user's question.")


class CitationResponse(BaseModel):
    """A citation supporting an answer."""

    doc_id: str
    chunk_id: str
    section: str = ""
    page: int
    quote: str
    score: float


class ChatResponse(BaseModel):
    """The answer plus supporting citations."""

    answer: str
    citations: list[CitationResponse]
