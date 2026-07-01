"""Chat API route: evidence-first Q&A over a single document."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, require_min_role
from app.core.db import get_db
from app.core.permissions import require_knowledge_base_access
from app.repositories import document_repo, knowledge_base_repo
from app.schemas.chat import ChatRequest, ChatResponse, CitationResponse
from app.services import chat_service, chat_trace_service, question_log_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("user")),
) -> ChatResponse:
    """Answer a question about a document or knowledge base."""
    if request.doc_id:
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
        if getattr(doc, "lifecycle_status", "active") != "active":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Document is not active "
                    f"(lifecycle_status: {doc.lifecycle_status})."
                ),
            )
        require_knowledge_base_access(
            db,
            current_user,
            getattr(doc, "knowledge_base_id", None),
        )
        result = chat_service.answer_question(
            request.question,
            db=db,
            doc_id=request.doc_id,
        )
    else:
        knowledge_base = knowledge_base_repo.get_knowledge_base(
            db, request.knowledge_base_id or ""
        )
        if knowledge_base is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base not found: {request.knowledge_base_id}",
            )
        require_knowledge_base_access(db, current_user, request.knowledge_base_id)
        result = chat_service.answer_question(
            request.question,
            db=db,
            knowledge_base_id=request.knowledge_base_id,
        )
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
    question_log_id = None
    try:
        question_log = question_log_service.create_question_log(
            db,
            doc_id=request.doc_id,
            knowledge_base_id=request.knowledge_base_id,
            question=request.question,
            answer=result.answer,
            answer_status=result.answer_status,
            citations_json=[citation.model_dump() for citation in citations],
        )
        question_log_id = question_log.question_log_id
        chat_trace_service.create_chat_trace(
            db,
            question_log_id=question_log_id,
            query=request.question,
            result=result,
            retrieval=result.retrieval,
            model="",
            latency_ms=0,
        )
    except Exception:  # noqa: BLE001
        question_log_id = None
    return ChatResponse(
        answer=result.answer,
        citations=citations,
        trace=result.trace,
        question_log_id=question_log_id,
    )
