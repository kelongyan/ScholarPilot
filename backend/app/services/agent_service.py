"""Controlled Phase 5 Agent orchestration.

The first Phase 5 slice uses an in-repo state-machine style workflow. It keeps
the Agent boundary explicit so LangGraph can replace the runner later without
changing API contracts.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import AgentRun, AgentStep
from app.repositories import agent_run_repo
from app.schemas.agent import AgentRunResponse, AgentStepResponse
from app.schemas.chat import CitationResponse
from app.schemas.rag import RetrievalTraceResponse
from app.services import chat_service
from app.services.chat_service import ChatResult
from app.services.retrieval_service import RetrievalResult, run_hybrid_retrieval
from app.services.vector_service import RetrievedChunk

_COMPLEXITY_MARKERS = {
    "analyze",
    "analysis",
    "compare",
    "contrast",
    "difference",
    "differences",
    "trend",
    "trends",
    "tradeoff",
    "tradeoffs",
    "risk",
    "risks",
    "summarize",
    "synthesize",
    "recommend",
    "recommendation",
    "strategy",
    "plan",
    "steps",
    "why",
    "how",
    "对比",
    "比较",
    "差异",
    "趋势",
    "分析",
    "总结",
    "归纳",
    "建议",
    "风险",
    "方案",
    "步骤",
    "取舍",
}


@dataclass
class AgentStepResult:
    """In-memory Agent step trace."""

    sequence: int
    agent_name: str
    status: str
    input_json: dict[str, object] = field(default_factory=dict)
    output_json: dict[str, object] = field(default_factory=dict)
    latency_ms: int = 0
    error_message: str = ""


@dataclass
class AgentRunResult:
    """In-memory result for a controlled Agent workflow."""

    run_id: str
    route: str
    status: str
    doc_id: str | None
    knowledge_base_id: str | None
    question: str
    answer: str
    answer_status: str
    citations: list[CitationResponse]
    trace: RetrievalTraceResponse | None
    agent_steps: list[AgentStepResult]
    total_latency_ms: int
    chat_result: ChatResult | None = None
    retrieval: RetrievalResult | None = None
    question_log_id: str | None = None
    chat_trace_id: str | None = None


def run_agent_workflow(
    *,
    db: Session,
    question: str,
    doc_id: str | None = None,
    knowledge_base_id: str | None = None,
    mode: str = "auto",
    max_steps: int = 5,
) -> AgentRunResult:
    """Run a bounded Agent workflow over a document or knowledge base."""
    started_at = time.perf_counter()
    run_id = str(uuid.uuid4())
    route = _select_route(question, mode)
    steps: list[AgentStepResult] = []
    planned_agents = _plan_for_route(route)

    planner_output = {
        "route": route,
        "reason": _route_reason(question, mode, route),
        "planned_agents": planned_agents,
        "max_steps": max_steps,
    }
    steps.append(
        AgentStepResult(
            sequence=1,
            agent_name="planner_agent",
            status="completed",
            input_json={
                "question": question,
                "mode": mode,
                "doc_id": doc_id,
                "knowledge_base_id": knowledge_base_id,
            },
            output_json=planner_output,
        )
    )

    executable_agents = planned_agents[: max(0, max_steps - 1)]
    retrieval: RetrievalResult | None = None
    chat_result: ChatResult | None = None
    final_status = "completed"
    answer = "Agent workflow stopped before producing a final answer."
    answer_status = "max_steps_exceeded"
    citations: list[CitationResponse] = []
    trace: RetrievalTraceResponse | None = None

    if len(executable_agents) < len(planned_agents):
        final_status = "max_steps_exceeded"

    sequence = 2
    for agent_name in executable_agents:
        if agent_name == "retrieval_agent":
            retrieval, step = _timed_step(
                sequence=sequence,
                agent_name=agent_name,
                input_json={
                    "question": question,
                    "doc_id": doc_id,
                    "knowledge_base_id": knowledge_base_id,
                },
                action=lambda: _run_retrieval_step(
                    db=db,
                    question=question,
                    doc_id=doc_id,
                    knowledge_base_id=knowledge_base_id,
                ),
            )
            steps.append(step)
            if step.status == "failed":
                final_status = "failed"
                answer = f"Agent workflow failed during retrieval: {step.error_message}"
                answer_status = "failed"
                break
            if retrieval is not None:
                trace = retrieval.to_trace(question)
        elif agent_name == "analyst_agent":
            _analysis, step = _timed_step(
                sequence=sequence,
                agent_name=agent_name,
                input_json={"evidence_count": len(retrieval.evidence_pack) if retrieval else 0},
                action=lambda: _run_analysis_step(retrieval),
            )
            steps.append(step)
            if step.status == "failed":
                final_status = "failed"
                answer = f"Agent workflow failed during analysis: {step.error_message}"
                answer_status = "failed"
                break
        elif agent_name == "writer_agent":
            chat_result, step = _timed_step(
                sequence=sequence,
                agent_name=agent_name,
                input_json={
                    "question": question,
                    "evidence_count": len(retrieval.evidence_pack) if retrieval else 0,
                },
                action=lambda: _run_writer_step(question, retrieval),
            )
            steps.append(step)
            if step.status == "failed":
                final_status = "failed"
                answer = f"Agent workflow failed during writing: {step.error_message}"
                answer_status = "failed"
                break
            if chat_result is not None:
                answer = chat_result.answer
                answer_status = chat_result.answer_status
                citations = _to_citation_responses(chat_result.citations)
                trace = chat_result.trace
        elif agent_name == "reviewer_agent":
            _review, step = _timed_step(
                sequence=sequence,
                agent_name=agent_name,
                input_json={
                    "answer_status": chat_result.answer_status if chat_result else "",
                    "citation_count": len(chat_result.citations) if chat_result else 0,
                },
                action=lambda: _run_reviewer_step(chat_result, retrieval),
            )
            steps.append(step)
            if step.status == "failed":
                final_status = "failed"
                answer = f"Agent workflow failed during review: {step.error_message}"
                answer_status = "failed"
                break
        sequence += 1

    total_latency_ms = _elapsed_ms(started_at)
    return AgentRunResult(
        run_id=run_id,
        route=route,
        status=final_status,
        doc_id=doc_id,
        knowledge_base_id=knowledge_base_id,
        question=question,
        answer=answer,
        answer_status=answer_status,
        citations=citations,
        trace=trace,
        agent_steps=steps,
        total_latency_ms=total_latency_ms,
        chat_result=chat_result,
        retrieval=retrieval,
    )


def create_agent_run(
    db: Session,
    result: AgentRunResult,
    *,
    question_log_id: str | None = None,
    chat_trace_id: str | None = None,
) -> AgentRun:
    """Persist an Agent run and its step trace."""
    result.question_log_id = question_log_id
    result.chat_trace_id = chat_trace_id
    run = AgentRun(
        run_id=result.run_id,
        question_log_id=question_log_id,
        chat_trace_id=chat_trace_id,
        doc_id=result.doc_id,
        knowledge_base_id=result.knowledge_base_id,
        question=result.question,
        route=result.route,
        status=result.status,
        answer_status=result.answer_status,
        answer=result.answer,
        citations_json=[citation.model_dump() for citation in result.citations],
        trace_json=result.trace.model_dump() if result.trace else {},
        total_latency_ms=result.total_latency_ms,
    )
    steps = [
        AgentStep(
            run_id=result.run_id,
            sequence=step.sequence,
            agent_name=step.agent_name,
            status=step.status,
            input_json=step.input_json,
            output_json=step.output_json,
            latency_ms=step.latency_ms,
            error_message=step.error_message,
        )
        for step in result.agent_steps
    ]
    return agent_run_repo.create_agent_run(db, run, steps)


def list_agent_run_responses(db: Session) -> list[AgentRunResponse]:
    """List persisted Agent runs with their step traces."""
    responses: list[AgentRunResponse] = []
    for run in agent_run_repo.list_agent_runs(db):
        steps = agent_run_repo.list_agent_steps(db, run.run_id)
        responses.append(_response_from_persisted(run, steps))
    return responses


def get_agent_run_response(db: Session, run_id: str) -> AgentRunResponse | None:
    """Get a persisted Agent run with its step trace."""
    run = agent_run_repo.get_agent_run(db, run_id)
    if run is None:
        return None
    steps = agent_run_repo.list_agent_steps(db, run.run_id)
    return _response_from_persisted(run, steps)


def response_from_result(result: AgentRunResult) -> AgentRunResponse:
    """Convert an in-memory Agent run to an API response."""
    return AgentRunResponse(
        run_id=result.run_id,
        route=result.route,
        status=result.status,
        doc_id=result.doc_id,
        knowledge_base_id=result.knowledge_base_id,
        question=result.question,
        answer=result.answer,
        answer_status=result.answer_status,
        citations=result.citations,
        trace=result.trace,
        agent_steps=[_step_response(step) for step in result.agent_steps],
        question_log_id=result.question_log_id,
        chat_trace_id=result.chat_trace_id,
        total_latency_ms=result.total_latency_ms,
    )


def _select_route(question: str, mode: str) -> str:
    if mode == "short":
        return "short"
    if mode == "multi_agent":
        return "multi_agent"
    return "multi_agent" if _is_complex_question(question) else "short"


def _is_complex_question(question: str) -> bool:
    normalized = question.lower()
    if any(marker in normalized for marker in _COMPLEXITY_MARKERS):
        return True
    return len(normalized.split()) >= 18


def _route_reason(question: str, mode: str, route: str) -> str:
    if mode != "auto":
        return f"Mode forced route: {route}."
    if route == "multi_agent":
        return "Question appears analytical or multi-step, so the multi-agent route was selected."
    return "Question appears direct, so the short route was selected."


def _plan_for_route(route: str) -> list[str]:
    if route == "multi_agent":
        return ["retrieval_agent", "analyst_agent", "writer_agent", "reviewer_agent"]
    return ["retrieval_agent", "writer_agent"]


def _timed_step[T](
    *,
    sequence: int,
    agent_name: str,
    input_json: dict[str, object],
    action: Callable[[], tuple[T, dict[str, object]]],
) -> tuple[T | None, AgentStepResult]:
    started_at = time.perf_counter()
    try:
        value, output_json = action()
        return value, AgentStepResult(
            sequence=sequence,
            agent_name=agent_name,
            status="completed",
            input_json=input_json,
            output_json=output_json,
            latency_ms=_elapsed_ms(started_at),
        )
    except Exception as exc:  # noqa: BLE001
        return None, AgentStepResult(
            sequence=sequence,
            agent_name=agent_name,
            status="failed",
            input_json=input_json,
            latency_ms=_elapsed_ms(started_at),
            error_message=str(exc),
        )


def _run_retrieval_step(
    *,
    db: Session,
    question: str,
    doc_id: str | None,
    knowledge_base_id: str | None,
) -> tuple[RetrievalResult, dict[str, object]]:
    retrieval = run_hybrid_retrieval(
        db,
        question=question,
        doc_id=doc_id,
        knowledge_base_id=knowledge_base_id,
    )
    return retrieval, {
        "rewritten_query": retrieval.rewritten_query,
        "dense_results": len(retrieval.dense_results),
        "sparse_results": len(retrieval.sparse_results),
        "fused_results": len(retrieval.fused_results),
        "reranked_results": len(retrieval.reranked_results),
        "evidence_count": len(retrieval.evidence_pack),
    }


def _run_analysis_step(
    retrieval: RetrievalResult | None,
) -> tuple[dict[str, object], dict[str, object]]:
    if retrieval is None:
        raise ValueError("retrieval result is required before analysis")

    evidence = retrieval.evidence_pack
    doc_ids = sorted({item.chunk.doc_id for item in evidence})
    pages = [item.chunk.page_start for item in evidence[:5]]
    sections = sorted({item.chunk.section for item in evidence if item.chunk.section})
    coverage = "sufficient" if len(evidence) >= 2 else "thin"
    output = {
        "evidence_count": len(evidence),
        "source_doc_count": len(doc_ids),
        "source_doc_ids": doc_ids,
        "top_pages": pages,
        "sections": sections[:5],
        "coverage": coverage,
        "analysis": (
            "Evidence spans multiple sources."
            if len(doc_ids) > 1
            else "Evidence comes from a single source."
        ),
    }
    return output, output


def _run_writer_step(
    question: str,
    retrieval: RetrievalResult | None,
) -> tuple[ChatResult, dict[str, object]]:
    if retrieval is None:
        raise ValueError("retrieval result is required before writing")
    result = chat_service.answer_from_retrieval(question, retrieval)
    return result, {
        "answer_status": result.answer_status,
        "citation_count": len(result.citations),
    }


def _run_reviewer_step(
    result: ChatResult | None,
    retrieval: RetrievalResult | None,
) -> tuple[dict[str, object], dict[str, object]]:
    if result is None or retrieval is None:
        raise ValueError("answer and retrieval result are required before review")

    evidence_chunk_ids = {item.chunk.chunk_id for item in retrieval.evidence_pack}
    unsupported = [
        citation.chunk_id
        for citation in result.citations
        if citation.chunk_id not in evidence_chunk_ids
    ]
    output = {
        "review_status": "passed" if not unsupported else "warning",
        "answer_status": result.answer_status,
        "citation_count": len(result.citations),
        "evidence_count": len(retrieval.evidence_pack),
        "unsupported_citation_count": len(unsupported),
        "unsupported_chunk_ids": unsupported,
    }
    return output, output


def _to_citation_responses(chunks: list[RetrievedChunk]) -> list[CitationResponse]:
    return [
        CitationResponse(
            doc_id=chunk.doc_id,
            chunk_id=chunk.chunk_id,
            section=chunk.section,
            page=chunk.page_start,
            quote=chunk.text[:400],
            score=chunk.score,
        )
        for chunk in chunks
    ]


def _response_from_persisted(
    run: AgentRun, steps: list[AgentStep]
) -> AgentRunResponse:
    trace = RetrievalTraceResponse.model_validate(run.trace_json) if run.trace_json else None
    return AgentRunResponse(
        run_id=run.run_id,
        route=run.route,
        status=run.status,
        doc_id=run.doc_id,
        knowledge_base_id=run.knowledge_base_id,
        question=run.question,
        answer=run.answer,
        answer_status=run.answer_status,
        citations=[
            CitationResponse.model_validate(citation)
            for citation in run.citations_json
        ],
        trace=trace,
        agent_steps=[
            AgentStepResponse(
                sequence=step.sequence,
                agent_name=step.agent_name,
                status=step.status,
                input_json=step.input_json,
                output_json=step.output_json,
                latency_ms=step.latency_ms,
                error_message=step.error_message,
            )
            for step in steps
        ],
        question_log_id=run.question_log_id,
        chat_trace_id=run.chat_trace_id,
        total_latency_ms=run.total_latency_ms,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _step_response(step: AgentStepResult) -> AgentStepResponse:
    return AgentStepResponse(
        sequence=step.sequence,
        agent_name=step.agent_name,
        status=step.status,
        input_json=step.input_json,
        output_json=step.output_json,
        latency_ms=step.latency_ms,
        error_message=step.error_message,
    )


def _elapsed_ms(started_at: float) -> int:
    return max(0, round((time.perf_counter() - started_at) * 1000))
