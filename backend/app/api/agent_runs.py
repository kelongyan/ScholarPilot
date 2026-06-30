"""Controlled Agent workflow API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repositories import document_repo, knowledge_base_repo
from app.schemas.agent import AgentRunListResponse, AgentRunRequest, AgentRunResponse
from app.services import (
    agent_service,
    audit_log_service,
    chat_trace_service,
    question_log_service,
)

router = APIRouter(prefix="/agent-runs", tags=["agent-runs"])


@router.post(
    "",
    response_model=AgentRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_agent(
    request: AgentRunRequest,
    db: Session = Depends(get_db),
) -> AgentRunResponse:
    """Run a bounded Agent workflow against a document or knowledge base."""
    doc_id, knowledge_base_id = _validate_scope(request, db)
    result = agent_service.run_agent_workflow(
        db=db,
        question=request.question,
        doc_id=doc_id,
        knowledge_base_id=knowledge_base_id,
        mode=request.mode,
        max_steps=request.max_steps,
    )

    question_log_id = None
    chat_trace_id = None
    if result.chat_result is not None and result.retrieval is not None:
        try:
            question_log = question_log_service.create_question_log(
                db,
                doc_id=doc_id,
                knowledge_base_id=knowledge_base_id,
                question=request.question,
                answer=result.chat_result.answer,
                answer_status=result.chat_result.answer_status,
                citations_json=[citation.model_dump() for citation in result.citations],
            )
            question_log_id = question_log.question_log_id
            chat_trace = chat_trace_service.create_chat_trace(
                db,
                question_log_id=question_log_id,
                query=request.question,
                result=result.chat_result,
                retrieval=result.retrieval,
                model="",
                latency_ms=result.total_latency_ms,
            )
            chat_trace_id = chat_trace.trace_id
        except Exception:  # noqa: BLE001
            question_log_id = None
            chat_trace_id = None

    agent_service.create_agent_run(
        db,
        result,
        question_log_id=question_log_id,
        chat_trace_id=chat_trace_id,
    )
    audit_log_service.try_log_event(
        db,
        action="agent_run.created",
        resource_type="agent_run",
        resource_id=result.run_id,
        knowledge_base_id=result.knowledge_base_id,
        detail_json={
            "doc_id": result.doc_id,
            "route": result.route,
            "status": result.status,
            "answer_status": result.answer_status,
            "question_log_id": question_log_id,
            "chat_trace_id": chat_trace_id,
            "step_count": len(result.agent_steps),
            "citation_count": len(result.citations),
            "total_latency_ms": result.total_latency_ms,
        },
    )

    return agent_service.response_from_result(result)


@router.get("", response_model=AgentRunListResponse)
async def list_agent_runs(
    knowledge_base_id: str | None = None,
    route: str | None = None,
    status: str | None = None,
    answer_status: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    db: Session = Depends(get_db),
) -> AgentRunListResponse:
    """List persisted Agent runs."""
    return AgentRunListResponse(
        agent_runs=agent_service.list_agent_run_responses(
            db,
            knowledge_base_id=knowledge_base_id,
            route=route,
            status=status,
            answer_status=answer_status,
            created_from=created_from,
            created_to=created_to,
        )
    )


@router.get("/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> AgentRunResponse:
    """Get a persisted Agent run with step trace."""
    result = agent_service.get_agent_run_response(db, run_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent run not found: {run_id}",
        )
    audit_log_service.try_log_event(
        db,
        action="agent_run.viewed",
        resource_type="agent_run",
        resource_id=result.run_id,
        knowledge_base_id=result.knowledge_base_id,
        detail_json={
            "doc_id": result.doc_id,
            "route": result.route,
            "status": result.status,
            "answer_status": result.answer_status,
            "step_count": len(result.agent_steps),
            "citation_count": len(result.citations),
        },
    )
    return result


def _validate_scope(
    request: AgentRunRequest,
    db: Session,
) -> tuple[str | None, str | None]:
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
        return request.doc_id, doc.knowledge_base_id

    knowledge_base = knowledge_base_repo.get_knowledge_base(
        db, request.knowledge_base_id or ""
    )
    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base not found: {request.knowledge_base_id}",
        )
    return None, request.knowledge_base_id
