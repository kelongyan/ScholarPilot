"""Document API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile,
    db: Session = Depends(get_db),
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
    document = document_service.upload_pdf(db, file)
    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    """List all documents, newest first."""
    docs = document_service.list_documents(db)
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs]
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: Session = Depends(get_db)) -> DocumentResponse:
    """Get a document's metadata and processing status."""
    doc = document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    return DocumentResponse.model_validate(doc)


@router.post("/{doc_id}/reindex", response_model=DocumentResponse)
async def reindex_document(
    doc_id: str, db: Session = Depends(get_db)
) -> DocumentResponse:
    """Re-enqueue parsing/indexing for an existing document."""
    doc = document_service.reindex_document(db, doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    return DocumentResponse.model_validate(doc)
