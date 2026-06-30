"""Document API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import (
    CurrentUser,
    filter_by_knowledge_base_access,
    require_knowledge_base_access,
    require_min_role,
)
from app.core.db import get_db
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services import audit_log_service, document_service, knowledge_base_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> DocumentResponse:
    """Upload a PDF and enqueue async parsing/indexing.

    Returns the created document with status ``uploaded``. Poll
    ``GET /documents/{doc_id}`` until ``status`` becomes ``indexed``.
    """
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )
    if knowledge_base_id:
        kb = knowledge_base_service.get_knowledge_base(db, knowledge_base_id)
        if kb is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base not found: {knowledge_base_id}",
            )
        require_knowledge_base_access(current_user, knowledge_base_id)
    elif current_user.knowledge_base_ids is not None and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Knowledge-base-scoped actors must upload to an explicit knowledge base.",
        )
    document = document_service.upload_pdf(
        db,
        file,
        knowledge_base_id=knowledge_base_id,
    )
    audit_log_service.try_log_event(
        db,
        action="document.uploaded",
        resource_type="document",
        resource_id=document.doc_id,
        knowledge_base_id=document.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={
            "title": document.title,
            "source": document.source,
            "status": document.status,
            "filename": file.filename or "",
        },
    )
    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    knowledge_base_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("user")),
) -> DocumentListResponse:
    """List documents, optionally filtered by knowledge base."""
    if knowledge_base_id:
        kb = knowledge_base_service.get_knowledge_base(db, knowledge_base_id)
        if kb is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base not found: {knowledge_base_id}",
            )
        require_knowledge_base_access(current_user, knowledge_base_id)
        docs = document_service.list_documents_by_knowledge_base(db, knowledge_base_id)
    else:
        docs = document_service.list_documents(db)
        docs = filter_by_knowledge_base_access(
            docs,
            current_user,
            get_knowledge_base_id=lambda doc: doc.knowledge_base_id,
        )
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs]
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("user")),
) -> DocumentResponse:
    """Get a document's metadata and processing status."""
    doc = document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    require_knowledge_base_access(current_user, doc.knowledge_base_id)
    return DocumentResponse.model_validate(doc)


@router.post("/{doc_id}/reindex", response_model=DocumentResponse)
async def reindex_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> DocumentResponse:
    """Re-enqueue parsing/indexing for an existing document."""
    existing = document_service.get_document(db, doc_id)
    if existing is not None:
        require_knowledge_base_access(current_user, existing.knowledge_base_id)
    previous_status = getattr(existing, "status", "") if existing is not None else ""
    doc = document_service.reindex_document(db, doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    audit_log_service.try_log_event(
        db,
        action="document.reindexed",
        resource_type="document",
        resource_id=doc.doc_id,
        knowledge_base_id=doc.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={
            "previous_status": previous_status,
            "status": doc.status,
            "title": doc.title,
        },
    )
    return DocumentResponse.model_validate(doc)
