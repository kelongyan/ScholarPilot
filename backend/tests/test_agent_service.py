"""Tests for controlled Phase 5 Agent orchestration."""

from __future__ import annotations

from app.services import agent_service, chat_service
from app.services.retrieval_service import RetrievalResult, RetrievedEvidence
from app.services.vector_service import RetrievedChunk


def _retrieval_result() -> RetrievalResult:
    chunk = RetrievedChunk(
        chunk_id="chunk-1",
        doc_id="doc-1",
        text="The incident process requires triage, owner assignment, and review.",
        section="Operations",
        page_start=2,
        page_end=2,
        chunk_type="paragraph",
        chunk_index=0,
        score=0.88,
    )
    evidence = RetrievedEvidence(chunk=chunk, retrieval_source="rerank")
    return RetrievalResult(
        rewritten_query="rewritten",
        dense_results=[evidence],
        sparse_results=[evidence],
        fused_results=[evidence],
        reranked_results=[evidence],
        evidence_pack=[evidence],
    )


def _patch_retrieval_and_llm(monkeypatch) -> None:
    monkeypatch.setattr(
        agent_service,
        "run_hybrid_retrieval",
        lambda db, question, doc_id=None, knowledge_base_id=None: _retrieval_result(),
    )

    class FakeLLM:
        def chat(self, messages, **kwargs):
            return "The process requires triage, owner assignment, and review."

    monkeypatch.setattr(chat_service, "get_llm_provider", lambda: FakeLLM())


def test_agent_workflow_routes_simple_questions_to_short_chain(monkeypatch) -> None:
    _patch_retrieval_and_llm(monkeypatch)

    result = agent_service.run_agent_workflow(
        db=object(),
        doc_id="doc-1",
        question="What does the process require?",
    )

    assert result.route == "short"
    assert result.status == "completed"
    assert result.answer_status == "answered"
    assert [step.agent_name for step in result.agent_steps] == [
        "planner_agent",
        "retrieval_agent",
        "writer_agent",
    ]
    assert result.citations[0].chunk_id == "chunk-1"
    assert result.trace is not None


def test_agent_workflow_routes_complex_questions_to_multi_agent_chain(monkeypatch) -> None:
    _patch_retrieval_and_llm(monkeypatch)

    result = agent_service.run_agent_workflow(
        db=object(),
        knowledge_base_id="kb-1",
        question="Compare the risks and recommend the next operational steps.",
    )

    assert result.route == "multi_agent"
    assert result.status == "completed"
    assert [step.agent_name for step in result.agent_steps] == [
        "planner_agent",
        "retrieval_agent",
        "analyst_agent",
        "writer_agent",
        "reviewer_agent",
    ]
    assert result.agent_steps[-1].output_json["review_status"] == "passed"


def test_agent_workflow_enforces_max_steps(monkeypatch) -> None:
    _patch_retrieval_and_llm(monkeypatch)

    result = agent_service.run_agent_workflow(
        db=object(),
        knowledge_base_id="kb-1",
        question="Compare the risks and recommend the next operational steps.",
        mode="multi_agent",
        max_steps=3,
    )

    assert result.status == "max_steps_exceeded"
    assert result.answer_status == "max_steps_exceeded"
    assert [step.agent_name for step in result.agent_steps] == [
        "planner_agent",
        "retrieval_agent",
        "analyst_agent",
    ]
    assert "stopped before producing" in result.answer


def test_create_agent_run_serializes_steps(monkeypatch) -> None:
    _patch_retrieval_and_llm(monkeypatch)
    result = agent_service.run_agent_workflow(
        db=object(),
        doc_id="doc-1",
        question="What does the process require?",
    )

    class FakeDB:
        def __init__(self) -> None:
            self.items = []

        def add(self, obj) -> None:
            self.items.append(obj)

        def commit(self) -> None:
            pass

        def refresh(self, obj) -> None:
            pass

    db = FakeDB()
    run = agent_service.create_agent_run(
        db,
        result,
        question_log_id="ql-1",
        chat_trace_id="trace-1",
    )

    assert run.run_id == result.run_id
    assert run.question_log_id == "ql-1"
    assert run.chat_trace_id == "trace-1"
    assert len(db.items) == 1 + len(result.agent_steps)
