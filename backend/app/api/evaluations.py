"""Evaluation API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, require_min_role
from app.core.db import get_db
from app.core.permissions import require_knowledge_base_access
from app.repositories import document_repo, knowledge_base_repo
from app.schemas.evaluation import (
    EvaluationDatasetDetailResponse,
    EvaluationDatasetListResponse,
    EvaluationExecutionMode,
    EvaluationRunCreateRequest,
    EvaluationRunListResponse,
    EvaluationRunResponse,
)
from app.services import audit_log_service, evaluation_service

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/datasets", response_model=EvaluationDatasetListResponse)
async def list_datasets(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("user")),
) -> EvaluationDatasetListResponse:
    """List evaluation datasets."""
    _ = current_user
    return EvaluationDatasetListResponse(
        evaluation_datasets=evaluation_service.list_datasets(db)
    )


@router.get("/datasets/{dataset_key}", response_model=EvaluationDatasetDetailResponse)
async def get_dataset(
    dataset_key: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("user")),
) -> EvaluationDatasetDetailResponse:
    """Get a dataset and its questions."""
    _ = current_user
    dataset = evaluation_service.get_dataset_detail(db, dataset_key)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation dataset not found: {dataset_key}",
        )
    return dataset


@router.post("/runs", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    request: EvaluationRunCreateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> EvaluationRunResponse:
    """Execute a repeatable evaluation run."""
    request = _validate_scope(request, db)
    require_knowledge_base_access(
        db,
        current_user,
        request.knowledge_base_id,
        min_member_role="manager",
    )
    try:
        run = evaluation_service.run_evaluation(db, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_log_service.try_log_event(
        db,
        action="evaluation_run.created",
        resource_type="evaluation_run",
        resource_id=run.run_id,
        knowledge_base_id=run.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={
            "dataset_key": run.dataset_key,
            "doc_id": run.doc_id,
            "execution_mode": run.execution_mode,
            "status": run.status,
            "question_count": run.question_count,
            "passed_count": run.passed_count,
            "failed_count": run.failed_count,
            "pass_rate": run.pass_rate,
            "average_latency_ms": run.average_latency_ms,
        },
    )
    return run


@router.get("/runs", response_model=EvaluationRunListResponse)
async def list_runs(
    dataset_key: str | None = None,
    knowledge_base_id: str | None = None,
    doc_id: str | None = None,
    execution_mode: EvaluationExecutionMode | None = None,
    status: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> EvaluationRunListResponse:
    """List persisted evaluation runs."""
    require_knowledge_base_access(db, current_user, knowledge_base_id)
    if knowledge_base_id is None and current_user.knowledge_base_ids is not None:
        runs = []
        for allowed_knowledge_base_id in sorted(current_user.knowledge_base_ids):
            runs.extend(
                evaluation_service.list_runs(
                    db,
                    dataset_key=dataset_key,
                    knowledge_base_id=allowed_knowledge_base_id,
                    doc_id=doc_id,
                    execution_mode=execution_mode,
                    status=status,
                    created_from=created_from,
                    created_to=created_to,
                )
            )
        return EvaluationRunListResponse(evaluation_runs=runs)
    return EvaluationRunListResponse(
        evaluation_runs=evaluation_service.list_runs(
            db,
            dataset_key=dataset_key,
            knowledge_base_id=knowledge_base_id,
            doc_id=doc_id,
            execution_mode=execution_mode,
            status=status,
            created_from=created_from,
            created_to=created_to,
        )
    )


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_min_role("kb_manager")),
) -> EvaluationRunResponse:
    """Get a persisted evaluation run with its question results."""
    run = evaluation_service.get_run_response(db, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run not found: {run_id}",
        )
    require_knowledge_base_access(db, current_user, run.knowledge_base_id)
    audit_log_service.try_log_event(
        db,
        action="evaluation_run.viewed",
        resource_type="evaluation_run",
        resource_id=run.run_id,
        knowledge_base_id=run.knowledge_base_id,
        actor_id=current_user.actor_id,
        detail_json={
            "dataset_key": run.dataset_key,
            "doc_id": run.doc_id,
            "execution_mode": run.execution_mode,
            "status": run.status,
            "question_count": run.question_count,
            "passed_count": run.passed_count,
            "failed_count": run.failed_count,
            "pass_rate": run.pass_rate,
        },
    )
    return run


def _validate_scope(
    request: EvaluationRunCreateRequest,
    db: Session,
) -> EvaluationRunCreateRequest:
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
                detail=(
                    f"Document is not indexed (status: {doc.status}). "
                    "Wait for indexing to complete."
                ),
            )
        if getattr(doc, "lifecycle_status", "active") != "active":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Document is not active "
                    f"(lifecycle_status: {doc.lifecycle_status})."
                ),
            )
        return request.model_copy(update={"knowledge_base_id": doc.knowledge_base_id})

    knowledge_base = knowledge_base_repo.get_knowledge_base(
        db, request.knowledge_base_id or ""
    )
    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {request.knowledge_base_id}",
        )
    return request
