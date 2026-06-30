"""Persisted chat trace service."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models import ChatTrace
from app.repositories import chat_trace_repo
from app.services.chat_service import ChatResult
from app.services.retrieval_service import RetrievalResult


def create_chat_trace(
    db: Session,
    *,
    question_log_id: str,
    query: str,
    result: ChatResult,
    retrieval: RetrievalResult,
    model: str = "",
    latency_ms: int = 0,
) -> ChatTrace:
    trace = ChatTrace(
        trace_id=str(uuid.uuid4()),
        question_log_id=question_log_id,
        query=query,
        rewritten_query=retrieval.rewritten_query,
        dense_results_json=_serialize_hits(retrieval.dense_results),
        sparse_results_json=_serialize_hits(retrieval.sparse_results),
        fused_results_json=_serialize_hits(retrieval.fused_results),
        reranked_results_json=_serialize_hits(retrieval.reranked_results),
        evidence_pack_json=_serialize_hits(retrieval.evidence_pack),
        answer=result.answer,
        citations_json=[_serialize_citation(c) for c in result.citations],
        answer_status=result.answer_status,
        model=model,
        latency_ms=latency_ms,
    )
    return chat_trace_repo.create_chat_trace(db, trace)


def list_chat_traces(db: Session) -> list[ChatTrace]:
    return chat_trace_repo.list_chat_traces(db)


def get_chat_trace(db: Session, trace_id: str) -> ChatTrace | None:
    return chat_trace_repo.get_chat_trace(db, trace_id)


def get_chat_trace_by_question_log_id(
    db: Session, question_log_id: str
) -> ChatTrace | None:
    return chat_trace_repo.get_chat_trace_by_question_log_id(db, question_log_id)


def _serialize_hits(items) -> list[dict[str, object]]:
    return [
        {
            "doc_id": item.chunk.doc_id,
            "chunk_id": item.chunk.chunk_id,
            "section": item.chunk.section,
            "page_start": item.chunk.page_start,
            "page_end": item.chunk.page_end,
            "chunk_type": item.chunk.chunk_type,
            "chunk_index": item.chunk.chunk_index,
            "score": item.chunk.score,
            "retrieval_source": item.retrieval_source,
            "text": item.chunk.text,
        }
        for item in items
    ]


def _serialize_citation(citation) -> dict[str, object]:
    return {
        "doc_id": citation.doc_id,
        "chunk_id": citation.chunk_id,
        "section": citation.section,
        "page": getattr(citation, "page", citation.page_start),
        "quote": getattr(citation, "quote", citation.text[:400]),
        "score": citation.score,
    }
