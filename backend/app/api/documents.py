"""Document API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import (
    CurrentUser,
    require_min_role,
)
from app.core.db import get_db
from app.core.permissions import (
    filter_by_knowledge_base_access,
    require_knowledge_base_access,
)
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services import audit_log_service, document_service, knowledge_base_service
from app.services.parser_service import (
    SUPPORTED_DOCUMENT_EXTENSIONS_LABEL,
    get_supported_document_source,
)

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
    """Upload a supported document and enqueue async parsing/indexing.

    Returns the created document with status ``uploaded``. Poll
    ``GET /documents/{doc_id}`` until ``status`` becomes ``indexed``.
    """
    source = get_supported_document_source(file.filename or "")
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supported file types: {SUPPORTED_DOCUMENT_EXTENSIONS_LABEL}.",
        )
    if knowledge_base_id:
        kb = knowledge_base_service.get_knowledge_base(db, knowledge_base_id)
        if kb is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base not found: {knowledge_base_id}",
            )
        require_knowledge_base_access(
            db,
            current_user,
            knowledge_base_id,
            min_member_role="contributor",
        )
    elif current_user.knowledge_base_ids is not None and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Knowledge-base-scoped actors must upload to an explicit knowledge base.",
        )
    document = document_service.upload_document(
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
            "detected_source": source,
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
        require_knowledge_base_access(db, current_user, knowledge_base_id)
        docs = document_service.list_documents_by_knowledge_base(db, knowledge_base_id)
    else:
        docs = document_service.list_documents(db)
        docs = filter_by_knowledge_base_access(
            db,
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
    if _is_deleted_document(doc):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    require_knowledge_base_access(db, current_user, doc.knowledge_base_id)
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
        require_knowledge_base_access(
            db,
            current_user,
            existing.knowledge_base_id,
            min_member_role="manager",
        )
        _require_active_document(existing)
    previous_status = getattr(existing, "status", "") if existing is not None else ""
    try:
        doc = document_service.reindex_document(db, doc_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
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


@router.post("/{doc_id}/replace", response_model=DocumentResponse)
async def replace_document(
    doc_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> DocumentResponse:
    """Upload a replacement version and archive the previous document."""
    source = get_supported_document_source(file.filename or "")
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supported file types: {SUPPORTED_DOCUMENT_EXTENSIONS_LABEL}.",
        )
    existing = _get_document_or_404(db, doc_id)
    require_knowledge_base_access(
        db,
        current_user,
        existing.knowledge_base_id,
        min_member_role="manager",
    )
    _require_active_document(existing)
    try:
        replacement = document_service.replace_document(db, doc_id, file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if replacement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    audit_log_service.try_log_event(
        db,
        action="document.replaced",
        resource_type="document",
        resource_id=replacement.doc_id,
        knowledge_base_id=replacement.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={
            "previous_doc_id": doc_id,
            "replacement_doc_id": replacement.doc_id,
            "source": replacement.source,
            "version": replacement.version,
            "filename": file.filename or "",
        },
    )
    return DocumentResponse.model_validate(replacement)


@router.post("/{doc_id}/archive", response_model=DocumentResponse)
async def archive_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> DocumentResponse:
    """Archive a document and remove its chunks/vectors from retrieval."""
    existing = _get_document_or_404(db, doc_id)
    require_knowledge_base_access(
        db,
        current_user,
        existing.knowledge_base_id,
        min_member_role="manager",
    )
    if getattr(existing, "lifecycle_status", "active") == "archived":
        return DocumentResponse.model_validate(existing)
    _require_active_document(existing)
    doc = document_service.archive_document(db, doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    audit_log_service.try_log_event(
        db,
        action="document.archived",
        resource_type="document",
        resource_id=doc.doc_id,
        knowledge_base_id=doc.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={"title": doc.title, "version": doc.version},
    )
    return DocumentResponse.model_validate(doc)


@router.post("/{doc_id}/restore", response_model=DocumentResponse)
async def restore_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> DocumentResponse:
    """Restore an archived document and queue reindexing."""
    existing = _get_document_or_404(db, doc_id)
    require_knowledge_base_access(
        db,
        current_user,
        existing.knowledge_base_id,
        min_member_role="manager",
    )
    if getattr(existing, "lifecycle_status", "active") == "active":
        return DocumentResponse.model_validate(existing)
    if _is_deleted_document(existing):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    doc = document_service.restore_document(db, doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    audit_log_service.try_log_event(
        db,
        action="document.restored",
        resource_type="document",
        resource_id=doc.doc_id,
        knowledge_base_id=doc.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={"title": doc.title, "version": doc.version, "status": doc.status},
    )
    return DocumentResponse.model_validate(doc)


@router.delete("/{doc_id}", response_model=DocumentResponse)
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> DocumentResponse:
    """Soft-delete a document and remove its chunks/vectors from retrieval."""
    existing = _get_document_or_404(db, doc_id)
    require_knowledge_base_access(
        db,
        current_user,
        existing.knowledge_base_id,
        min_member_role="manager",
    )
    doc = document_service.delete_document(db, doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    audit_log_service.try_log_event(
        db,
        action="document.deleted",
        resource_type="document",
        resource_id=doc.doc_id,
        knowledge_base_id=doc.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={"title": doc.title, "version": doc.version},
    )
    return DocumentResponse.model_validate(doc)


def _get_document_or_404(db: Session, doc_id: str):
    doc = document_service.get_document(db, doc_id)
    if doc is None or _is_deleted_document(doc):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )
    return doc


def _require_active_document(doc) -> None:
    lifecycle_status = getattr(doc, "lifecycle_status", "active")
    if lifecycle_status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document is not active (lifecycle_status: {lifecycle_status}).",
        )


def _is_deleted_document(doc) -> bool:
    return getattr(doc, "lifecycle_status", "active") == "deleted"
