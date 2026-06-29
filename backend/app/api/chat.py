"""Chat API route: evidence-first Q&A over a single document."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repositories import document_repo
from app.schemas.chat import ChatRequest, ChatResponse, CitationResponse
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Answer a question about a document using evidence-first RAG.

    The document must be indexed (``status == indexed``) before querying.
    """
    doc = document_repo.get_document(db, request.doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {request.doc_id}",
        )
    if doc.status != "indexed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document is not indexed (status: {doc.status}). "
            "Wait for indexing to complete.",
        )

    result = chat_service.answer_question(request.doc_id, request.question)
    citations = [
        CitationResponse(
            doc_id=c.doc_id,
            chunk_id=c.chunk_id,
            section=c.section,
            page=c.page_start,
            quote=c.text[:400],
            score=c.score,
        )
        for c in result.citations
    ]
    return ChatResponse(answer=result.answer, citations=citations)
