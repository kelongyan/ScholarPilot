"""Tests for persisted chat trace service."""

from __future__ import annotations

from app.services.chat_service import ChatResult
from app.services.chat_trace_service import create_chat_trace
from app.services.retrieval_service import RetrievalResult, RetrievedEvidence
from app.services.vector_service import RetrievedChunk


class _FakeDB:
    def add(self, obj) -> None:
        self.obj = obj

    def commit(self) -> None:
        pass

    def refresh(self, obj) -> None:
        pass


def test_create_chat_trace_serializes_retrieval_data() -> None:
    db = _FakeDB()
    chunk = RetrievedChunk(
        chunk_id="chunk-1",
        doc_id="doc-1",
        text="evidence text",
        section="Method",
        page_start=3,
        page_end=3,
        chunk_type="paragraph",
        chunk_index=0,
        score=0.9,
    )
    evidence = RetrievedEvidence(chunk=chunk, retrieval_source="rerank")
    retrieval = RetrievalResult(
        rewritten_query="rewritten",
        dense_results=[evidence],
        sparse_results=[evidence],
        fused_results=[evidence],
        reranked_results=[evidence],
        evidence_pack=[evidence],
    )
    result = ChatResult(
        answer="grounded answer",
        citations=[chunk],
        trace=retrieval.to_trace("question"),
        retrieval=retrieval,
    )

    trace = create_chat_trace(
        db,
        question_log_id="ql-1",
        query="question",
        result=result,
        retrieval=result.retrieval,
        model="test-model",
        latency_ms=12,
    )

    assert trace.question_log_id == "ql-1"
    assert trace.rewritten_query == "rewritten"
    assert trace.answer == "grounded answer"
    assert trace.latency_ms == 12
