"""Evaluation dataset loading and repeatable run execution."""

from __future__ import annotations

import csv
import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import EvaluationDataset, EvaluationRun, EvaluationRunItem
from app.repositories import evaluation_repo
from app.schemas.evaluation import (
    EvaluationDatasetDetailResponse,
    EvaluationDatasetQuestionResponse,
    EvaluationDatasetResponse,
    EvaluationExecutionMode,
    EvaluationItemStatus,
    EvaluationRunCreateRequest,
    EvaluationRunItemResponse,
    EvaluationRunResponse,
    EvaluationRunStatus,
)
from app.schemas.rag import RetrievalTraceResponse
from app.services.agent_service import AgentRunResult, create_agent_run, run_agent_workflow
from app.services.chat_service import ChatResult
from app.services.chat_trace_service import create_chat_trace
from app.services.question_log_service import create_question_log
from app.services.retrieval_service import RetrievalResult, run_hybrid_retrieval

DEFAULT_PHASE2_DATASET_KEY = "phase2_fixed_qa"
DEFAULT_PHASE2_DATASET_NAME = "Phase 2 fixed QA set"
DEFAULT_PHASE2_DATASET_DESCRIPTION = "Repeatable evaluation set for Phase 2 regression checks."
DEFAULT_PHASE2_DATASET_SOURCE = "tests/fixtures/phase2_eval_questions.csv"

_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "tests"
    / "fixtures"
    / "phase2_eval_questions.csv"
)


@dataclass(frozen=True)
class EvaluationQuestionSpec:
    """Normalized dataset question specification."""

    sequence: int
    question: str
    expected_keywords: list[str]
    notes: str = ""


@dataclass(frozen=True)
class EvaluationQuestionResult:
    """Execution result for a single evaluation question."""

    sequence: int
    question: str
    expected_keywords: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    metrics_json: dict[str, object]
    answer: str
    answer_status: str
    execution_route: str
    status: str
    error_message: str
    latency_ms: int
    question_log_id: str | None
    chat_trace_id: str | None
    agent_run_id: str | None


def load_phase2_eval_questions() -> list[dict[str, str]]:
    """Load the repeatable Phase 2 evaluation question CSV."""
    with _FIXTURE_PATH.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def list_datasets(db: Session) -> list[EvaluationDatasetResponse]:
    """List evaluation datasets, seeding the Phase 2 dataset if needed."""
    _ensure_phase2_dataset(db)
    return [_dataset_response(dataset) for dataset in evaluation_repo.list_datasets(db)]


def get_dataset_detail(
    db: Session,
    dataset_key: str,
) -> EvaluationDatasetDetailResponse | None:
    """Get a dataset and its question definitions."""
    _ensure_phase2_dataset(db)
    dataset = evaluation_repo.get_dataset(db, dataset_key)
    if dataset is None:
        return None
    return _dataset_detail_response(dataset)


def list_runs(
    db: Session,
    *,
    dataset_key: str | None = None,
    knowledge_base_id: str | None = None,
    doc_id: str | None = None,
    execution_mode: EvaluationExecutionMode | None = None,
    status: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> list[EvaluationRunResponse]:
    """List persisted evaluation runs."""
    runs = evaluation_repo.list_runs(
        db,
        dataset_key=dataset_key,
        knowledge_base_id=knowledge_base_id,
        doc_id=doc_id,
        execution_mode=execution_mode,
        status=status,
        created_from=created_from,
        created_to=created_to,
    )
    return [_run_response(db, run) for run in runs]


def list_run_items(db: Session, run_id: str) -> list[EvaluationRunItemResponse]:
    """List persisted evaluation run items."""
    return [_run_item_response(item) for item in evaluation_repo.list_run_items(db, run_id)]


def get_run_response(db: Session, run_id: str) -> EvaluationRunResponse | None:
    """Get a persisted evaluation run with all run items."""
    run = evaluation_repo.get_run(db, run_id)
    if run is None:
        return None
    return _run_response(db, run)


def run_evaluation(
    db: Session,
    request: EvaluationRunCreateRequest,
) -> EvaluationRunResponse:
    """Execute a repeatable evaluation run and persist its artifacts."""
    dataset = evaluation_repo.get_dataset(db, request.dataset_key)
    if dataset is None:
        dataset = (
            _ensure_phase2_dataset(db)
            if request.dataset_key == DEFAULT_PHASE2_DATASET_KEY
            else None
        )
    if dataset is None:
        raise ValueError(f"Evaluation dataset not found: {request.dataset_key}")

    question_specs = _dataset_questions(dataset)
    dataset_version = _dataset_version(dataset)
    config_snapshot_json = _config_snapshot(
        request=request,
        dataset=dataset,
        dataset_version=dataset_version,
    )
    run = evaluation_repo.create_run(
        db,
        EvaluationRun(
            run_id=str(uuid.uuid4()),
            dataset_key=dataset.dataset_key,
            knowledge_base_id=request.knowledge_base_id,
            doc_id=request.doc_id,
            execution_mode=request.execution_mode,
            status="running",
            question_count=len(question_specs),
            passed_count=0,
            failed_count=0,
            average_latency_ms=0,
            dataset_version=dataset_version,
            config_snapshot_json=config_snapshot_json,
            summary_json={},
            metrics_json={},
        ),
    )

    results: list[EvaluationQuestionResult] = []
    answer_status_counts: dict[str, int] = {}
    route_counts: dict[str, int] = {}
    total_latency_ms = 0
    passed_count = 0
    failed_count = 0
    item_metrics: list[dict[str, object]] = []

    for spec in question_specs:
        result = _execute_question(
            db,
            request=request,
            sequence=spec.sequence,
            question=spec.question,
            expected_keywords=spec.expected_keywords,
            notes=spec.notes,
        )
        results.append(result)
        item_metrics.append(result.metrics_json)
        total_latency_ms += result.latency_ms
        answer_status_counts[result.answer_status] = (
            answer_status_counts.get(result.answer_status, 0) + 1
        )
        route_counts[result.execution_route] = route_counts.get(result.execution_route, 0) + 1
        if result.status == "passed":
            passed_count += 1
        else:
            failed_count += 1

        evaluation_repo.create_run_item(
            db,
            EvaluationRunItem(
                item_id=str(uuid.uuid4()),
                run_id=run.run_id,
                sequence=result.sequence,
                question=result.question,
                expected_keywords_json=result.expected_keywords,
                matched_keywords_json=result.matched_keywords,
                missing_keywords_json=result.missing_keywords,
                metrics_json=result.metrics_json,
                answer=result.answer,
                answer_status=result.answer_status,
                execution_route=result.execution_route,
                status=result.status,
                error_message=result.error_message,
                latency_ms=result.latency_ms,
                question_log_id=result.question_log_id,
                chat_trace_id=result.chat_trace_id,
                agent_run_id=result.agent_run_id,
            ),
        )

    question_count = len(results)
    average_latency_ms = round(total_latency_ms / question_count) if question_count else 0
    metrics_json = _run_metrics(item_metrics, total_latency_ms, question_count)
    summary_json = {
        "dataset_key": dataset.dataset_key,
        "dataset_version": dataset_version,
        "execution_mode": request.execution_mode,
        "knowledge_base_id": request.knowledge_base_id,
        "doc_id": request.doc_id,
        "question_count": question_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "pass_rate": round(passed_count / question_count, 3) if question_count else 0.0,
        "average_latency_ms": average_latency_ms,
        "answer_status_counts": answer_status_counts,
        "route_counts": route_counts,
        "metrics": metrics_json,
        "config_snapshot": config_snapshot_json,
    }
    evaluation_repo.update_run(
        db,
        run,
        status="completed",
        question_count=question_count,
        passed_count=passed_count,
        failed_count=failed_count,
        average_latency_ms=average_latency_ms,
        dataset_version=dataset_version,
        config_snapshot_json=config_snapshot_json,
        summary_json=summary_json,
        metrics_json=metrics_json,
    )
    return _run_response(db, run)


def _ensure_phase2_dataset(db: Session) -> EvaluationDataset:
    dataset = evaluation_repo.get_dataset(db, DEFAULT_PHASE2_DATASET_KEY)
    if dataset is not None:
        return dataset
    dataset = EvaluationDataset(
        dataset_key=DEFAULT_PHASE2_DATASET_KEY,
        name=DEFAULT_PHASE2_DATASET_NAME,
        description=DEFAULT_PHASE2_DATASET_DESCRIPTION,
        source_uri=DEFAULT_PHASE2_DATASET_SOURCE,
        questions_json=_phase2_question_payloads(),
    )
    return evaluation_repo.create_dataset(db, dataset)


def _phase2_question_payloads() -> list[dict[str, object]]:
    return [
        {
            "sequence": spec.sequence,
            "question": spec.question,
            "expected_keywords": spec.expected_keywords,
            "notes": spec.notes,
        }
        for spec in _phase2_question_specs()
    ]


def _phase2_question_specs() -> list[EvaluationQuestionSpec]:
    rows = load_phase2_eval_questions()
    specs: list[EvaluationQuestionSpec] = []
    for index, row in enumerate(rows, start=1):
        specs.append(
            EvaluationQuestionSpec(
                sequence=index,
                question=row.get("question", "").strip(),
                expected_keywords=_parse_keywords(row.get("expected_keywords", "")),
                notes=row.get("notes", "").strip(),
            )
        )
    return specs


def _dataset_questions(dataset: EvaluationDataset) -> list[EvaluationQuestionSpec]:
    questions: list[EvaluationQuestionSpec] = []
    for index, row in enumerate(dataset.questions_json, start=1):
        questions.append(
            EvaluationQuestionSpec(
                sequence=int(row.get("sequence", index)),
                question=str(row.get("question", "")).strip(),
                expected_keywords=[
                    str(keyword).strip()
                    for keyword in row.get("expected_keywords", [])
                    if str(keyword).strip()
                ],
                notes=str(row.get("notes", "")).strip(),
            )
        )
    return questions


def _execute_question(
    db: Session,
    *,
    request: EvaluationRunCreateRequest,
    sequence: int,
    question: str,
    expected_keywords: list[str],
    notes: str,
) -> EvaluationQuestionResult:
    started_at = time.perf_counter()
    question_log_id: str | None = None
    chat_trace_id: str | None = None
    agent_run_id: str | None = None
    execution_route = request.execution_mode
    answer = ""
    answer_status = "failed"
    error_message = ""
    trace_blob = ""
    trace: RetrievalTraceResponse | None = None
    citations_json: list[dict[str, object]] = []

    try:
        if request.execution_mode == "chat":
            retrieval = run_hybrid_retrieval(
                db,
                question=question,
                doc_id=request.doc_id,
                knowledge_base_id=request.knowledge_base_id,
            )
            chat_result = _answer_from_retrieval(question, retrieval)
            answer = chat_result.answer
            answer_status = chat_result.answer_status
            trace = chat_result.trace
            citations_json = _serialize_citations(chat_result.citations)
            trace_blob = _blob_from_chat_result(chat_result)
            question_log, chat_trace = _persist_answer_artifacts(
                db,
                question=question,
                request=request,
                result=chat_result,
                retrieval=retrieval,
            )
            question_log_id = question_log.question_log_id
            chat_trace_id = chat_trace.trace_id
            execution_route = "chat"
        else:
            agent_result = run_agent_workflow(
                db=db,
                question=question,
                doc_id=request.doc_id,
                knowledge_base_id=request.knowledge_base_id,
                mode="auto",
                max_steps=request.max_steps,
            )
            answer = agent_result.answer
            answer_status = agent_result.answer_status
            execution_route = agent_result.route
            trace = agent_result.trace
            citations_json = _serialize_citations(agent_result.citations)
            trace_blob = _blob_from_agent_result(agent_result)
            if agent_result.chat_result is not None and agent_result.retrieval is not None:
                question_log, chat_trace = _persist_answer_artifacts(
                    db,
                    question=question,
                    request=request,
                    result=agent_result.chat_result,
                    retrieval=agent_result.retrieval,
                )
                question_log_id = question_log.question_log_id
                chat_trace_id = chat_trace.trace_id
            created_run = create_agent_run(
                db,
                agent_result,
                question_log_id=question_log_id,
                chat_trace_id=chat_trace_id,
            )
            agent_run_id = created_run.run_id
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)

    latency_ms = _elapsed_ms(started_at)
    matched_keywords = _matched_keywords(expected_keywords, answer, trace_blob, notes)
    missing_keywords = [keyword for keyword in expected_keywords if keyword not in matched_keywords]
    metrics_json = _item_metrics(
        question=question,
        expected_keywords=expected_keywords,
        matched_keywords=matched_keywords,
        answer=answer,
        answer_status=answer_status,
        trace=trace,
        trace_blob=trace_blob,
        citations_json=citations_json,
        latency_ms=latency_ms,
        error_message=error_message,
    )
    if error_message:
        status = "error"
    elif missing_keywords or answer_status == "failed":
        status = "failed"
    else:
        status = "passed"

    return EvaluationQuestionResult(
        sequence=sequence,
        question=question,
        expected_keywords=expected_keywords,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        metrics_json=metrics_json,
        answer=answer,
        answer_status=answer_status,
        execution_route=execution_route,
        status=status,
        error_message=error_message,
        latency_ms=latency_ms,
        question_log_id=question_log_id,
        chat_trace_id=chat_trace_id,
        agent_run_id=agent_run_id,
    )


def _persist_answer_artifacts(
    db: Session,
    *,
    question: str,
    request: EvaluationRunCreateRequest,
    result: ChatResult,
    retrieval: RetrievalResult,
):
    question_log = create_question_log(
        db,
        doc_id=request.doc_id,
        knowledge_base_id=request.knowledge_base_id,
        question=question,
        answer=result.answer,
        answer_status=result.answer_status,
        citations_json=_serialize_citations(result.citations),
    )
    chat_trace = create_chat_trace(
        db,
        question_log_id=question_log.question_log_id,
        query=question,
        result=result,
        retrieval=retrieval,
        model="",
        latency_ms=0,
    )
    return question_log, chat_trace


def _matched_keywords(
    expected_keywords: list[str],
    answer: str,
    trace_blob: str,
    notes: str,
) -> list[str]:
    haystack = f"{answer}\n{trace_blob}\n{notes}".lower()
    return [keyword for keyword in expected_keywords if keyword.lower() in haystack]


def _blob_from_chat_result(result: ChatResult) -> str:
    payload = {
        "answer": result.answer,
        "answer_status": result.answer_status,
        "trace": result.trace.model_dump() if result.trace else {},
        "citations": _serialize_citations(result.citations),
    }
    return json.dumps(payload, ensure_ascii=False)


def _blob_from_agent_result(result: AgentRunResult) -> str:
    payload = {
        "answer": result.answer,
        "answer_status": result.answer_status,
        "route": result.route,
        "status": result.status,
        "trace": result.trace.model_dump() if result.trace else {},
        "citations": _serialize_citations(result.citations),
        "agent_steps": [step.__dict__ for step in result.agent_steps],
    }
    return json.dumps(payload, ensure_ascii=False)


def _dataset_response(dataset: EvaluationDataset) -> EvaluationDatasetResponse:
    return EvaluationDatasetResponse(
        dataset_key=dataset.dataset_key,
        name=dataset.name,
        description=dataset.description,
        source_uri=dataset.source_uri,
        question_count=len(dataset.questions_json),
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


def _dataset_detail_response(dataset: EvaluationDataset) -> EvaluationDatasetDetailResponse:
    return EvaluationDatasetDetailResponse(
        dataset_key=dataset.dataset_key,
        name=dataset.name,
        description=dataset.description,
        source_uri=dataset.source_uri,
        question_count=len(dataset.questions_json),
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        questions=[
            EvaluationDatasetQuestionResponse(
                sequence=int(row.get("sequence", index)),
                question=str(row.get("question", "")).strip(),
                expected_keywords=[
                    str(keyword).strip()
                    for keyword in row.get("expected_keywords", [])
                    if str(keyword).strip()
                ],
                notes=str(row.get("notes", "")).strip(),
            )
            for index, row in enumerate(dataset.questions_json, start=1)
        ],
    )


def _run_response(db: Session, run: EvaluationRun) -> EvaluationRunResponse:
    dataset = evaluation_repo.get_dataset(db, run.dataset_key)
    dataset_name = dataset.name if dataset else run.dataset_key
    items = evaluation_repo.list_run_items(db, run.run_id)
    response_items = [_run_item_response(item) for item in items]
    question_count = run.question_count or len(response_items)
    pass_rate = round(run.passed_count / question_count, 3) if question_count else 0.0
    previous_run = evaluation_repo.get_previous_completed_run(db, current_run=run)
    previous_run_id = previous_run.run_id if previous_run is not None else None
    metric_deltas = _metric_deltas(run, previous_run, pass_rate)
    return EvaluationRunResponse(
        run_id=run.run_id,
        dataset_key=run.dataset_key,
        dataset_name=dataset_name,
        knowledge_base_id=run.knowledge_base_id,
        doc_id=run.doc_id,
        execution_mode=cast(EvaluationExecutionMode, run.execution_mode),
        status=cast(EvaluationRunStatus, run.status),
        question_count=question_count,
        passed_count=run.passed_count,
        failed_count=run.failed_count,
        average_latency_ms=run.average_latency_ms,
        dataset_version=getattr(run, "dataset_version", "") or "",
        config_snapshot_json=getattr(run, "config_snapshot_json", {}) or {},
        pass_rate=pass_rate,
        summary_json=run.summary_json,
        metrics_json=getattr(run, "metrics_json", {}) or {},
        previous_run_id=previous_run_id,
        metric_deltas=metric_deltas,
        items=response_items,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _run_item_response(item: EvaluationRunItem) -> EvaluationRunItemResponse:
    return EvaluationRunItemResponse(
        item_id=item.item_id,
        sequence=item.sequence,
        question=item.question,
        expected_keywords=item.expected_keywords_json,
        matched_keywords=item.matched_keywords_json,
        missing_keywords=item.missing_keywords_json,
        metrics_json=getattr(item, "metrics_json", {}) or {},
        answer=item.answer,
        answer_status=item.answer_status,
        execution_route=item.execution_route,
        status=cast(EvaluationItemStatus, item.status),
        error_message=item.error_message,
        latency_ms=item.latency_ms,
        question_log_id=item.question_log_id,
        chat_trace_id=item.chat_trace_id,
        agent_run_id=item.agent_run_id,
        created_at=item.created_at,
    )


def _parse_keywords(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def _item_metrics(
    *,
    question: str,
    expected_keywords: list[str],
    matched_keywords: list[str],
    answer: str,
    answer_status: str,
    trace: RetrievalTraceResponse | None,
    trace_blob: str,
    citations_json: list[dict[str, object]],
    latency_ms: int,
    error_message: str,
) -> dict[str, object]:
    keyword_total = len(expected_keywords)
    keyword_coverage = round(len(matched_keywords) / keyword_total, 3) if keyword_total else 1.0
    answer_length = len(answer.strip())
    evidence_pack = trace.evidence_pack if trace is not None else []
    answer_keyword_matches = _matched_keywords(expected_keywords, answer, "", "")
    evidence_blob = "\n".join(item.text for item in evidence_pack)
    evidence_keyword_matches = _matched_keywords(expected_keywords, evidence_blob, "", "")
    evidence_chunk_ids = {item.chunk_id for item in evidence_pack}
    supported_citations = [
        citation
        for citation in citations_json
        if str(citation.get("chunk_id", "")) in evidence_chunk_ids
    ]
    estimated_prompt_tokens = _estimate_tokens(f"{question}\n{evidence_blob}")
    estimated_completion_tokens = _estimate_tokens(answer)
    return {
        "keyword_coverage": keyword_coverage,
        "expected_keyword_count": keyword_total,
        "matched_keyword_count": len(matched_keywords),
        "missing_keyword_count": max(0, keyword_total - len(matched_keywords)),
        "answer_relevance": _coverage(len(answer_keyword_matches), keyword_total),
        "recall_at_k": _coverage(len(evidence_keyword_matches), keyword_total),
        "mrr": _mean_reciprocal_rank(expected_keywords, trace),
        "citation_accuracy": _citation_accuracy(
            answer_status=answer_status,
            citation_count=len(citations_json),
            supported_citation_count=len(supported_citations),
        ),
        "citation_coverage": _citation_coverage(
            citation_count=len(citations_json),
            evidence_count=len(evidence_pack),
        ),
        "faithfulness": _faithfulness_proxy(
            answer_status=answer_status,
            answer_keyword_matches=answer_keyword_matches,
            evidence_keyword_matches=evidence_keyword_matches,
        ),
        "dense_hit_count": len(trace.dense_results) if trace is not None else 0,
        "sparse_hit_count": len(trace.sparse_results) if trace is not None else 0,
        "fused_hit_count": len(trace.fused_results) if trace is not None else 0,
        "reranked_hit_count": len(trace.reranked_results) if trace is not None else 0,
        "evidence_count": len(evidence_pack),
        "citation_count": len(citations_json),
        "supported_citation_count": len(supported_citations),
        "answer_length": answer_length,
        "has_answer": answer_status == "answered" and answer_length > 0,
        "has_trace": trace is not None or bool(trace_blob.strip()),
        "latency_ms": latency_ms,
        "error": bool(error_message),
        "estimated_prompt_tokens": estimated_prompt_tokens,
        "estimated_completion_tokens": estimated_completion_tokens,
        "estimated_total_tokens": estimated_prompt_tokens + estimated_completion_tokens,
        "estimated_cost_usd": 0.0,
        "cost_status": "placeholder",
    }


def _run_metrics(
    item_metrics: list[dict[str, object]],
    total_latency_ms: int,
    question_count: int,
) -> dict[str, object]:
    if question_count == 0:
        return {
            "average_keyword_coverage": 0.0,
            "average_recall_at_k": 0.0,
            "average_mrr": 0.0,
            "average_citation_accuracy": 0.0,
            "average_faithfulness": 0.0,
            "average_answer_relevance": 0.0,
            "answer_rate": 0.0,
            "trace_rate": 0.0,
            "error_rate": 0.0,
            "average_answer_length": 0,
            "average_latency_ms": 0,
            "max_latency_ms": 0,
            "estimated_total_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
    keyword_coverages = [float(metric.get("keyword_coverage", 0.0)) for metric in item_metrics]
    recall_scores = [float(metric.get("recall_at_k", 0.0)) for metric in item_metrics]
    mrr_scores = [float(metric.get("mrr", 0.0)) for metric in item_metrics]
    citation_accuracy_scores = [
        float(metric.get("citation_accuracy", 0.0)) for metric in item_metrics
    ]
    faithfulness_scores = [float(metric.get("faithfulness", 0.0)) for metric in item_metrics]
    answer_relevance_scores = [
        float(metric.get("answer_relevance", 0.0)) for metric in item_metrics
    ]
    answer_count = sum(1 for metric in item_metrics if metric.get("has_answer") is True)
    trace_count = sum(1 for metric in item_metrics if metric.get("has_trace") is True)
    error_count = sum(1 for metric in item_metrics if metric.get("error") is True)
    answer_lengths = [int(metric.get("answer_length", 0)) for metric in item_metrics]
    latencies = [int(metric.get("latency_ms", 0)) for metric in item_metrics]
    estimated_tokens = [int(metric.get("estimated_total_tokens", 0)) for metric in item_metrics]
    estimated_costs = [float(metric.get("estimated_cost_usd", 0.0)) for metric in item_metrics]
    return {
        "average_keyword_coverage": round(sum(keyword_coverages) / question_count, 3),
        "average_recall_at_k": round(sum(recall_scores) / question_count, 3),
        "average_mrr": round(sum(mrr_scores) / question_count, 3),
        "average_citation_accuracy": round(
            sum(citation_accuracy_scores) / question_count, 3
        ),
        "average_faithfulness": round(sum(faithfulness_scores) / question_count, 3),
        "average_answer_relevance": round(
            sum(answer_relevance_scores) / question_count, 3
        ),
        "answer_rate": round(answer_count / question_count, 3),
        "trace_rate": round(trace_count / question_count, 3),
        "error_rate": round(error_count / question_count, 3),
        "average_answer_length": round(sum(answer_lengths) / question_count),
        "average_latency_ms": round(total_latency_ms / question_count),
        "max_latency_ms": max(latencies) if latencies else 0,
        "estimated_total_tokens": sum(estimated_tokens),
        "estimated_cost_usd": round(sum(estimated_costs), 6),
        "cost_status": "placeholder",
    }


def _metric_deltas(
    run: EvaluationRun,
    previous_run: EvaluationRun | None,
    pass_rate: float,
) -> dict[str, float]:
    if previous_run is None:
        return {}
    previous_question_count = previous_run.question_count or 0
    previous_pass_rate = (
        round(previous_run.passed_count / previous_question_count, 3)
        if previous_question_count
        else 0.0
    )
    current_metrics = getattr(run, "metrics_json", {}) or {}
    previous_metrics = getattr(previous_run, "metrics_json", {}) or {}
    deltas = {
        "pass_rate": round(pass_rate - previous_pass_rate, 3),
        "average_latency_ms": float(run.average_latency_ms - previous_run.average_latency_ms),
    }
    for key in (
        "average_keyword_coverage",
        "average_recall_at_k",
        "average_mrr",
        "average_citation_accuracy",
        "average_faithfulness",
        "average_answer_relevance",
        "answer_rate",
        "trace_rate",
        "error_rate",
        "average_answer_length",
        "max_latency_ms",
        "estimated_total_tokens",
        "estimated_cost_usd",
    ):
        current_value = _numeric_metric(current_metrics.get(key))
        previous_value = _numeric_metric(previous_metrics.get(key))
        deltas[key] = round(current_value - previous_value, 3)
    return deltas


def _dataset_version(dataset: EvaluationDataset) -> str:
    payload = json.dumps(dataset.questions_json, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _config_snapshot(
    *,
    request: EvaluationRunCreateRequest,
    dataset: EvaluationDataset,
    dataset_version: str,
) -> dict[str, object]:
    settings = get_settings()
    return {
        "app_version": settings.app_version,
        "dataset": {
            "dataset_key": dataset.dataset_key,
            "dataset_version": dataset_version,
            "question_count": len(dataset.questions_json),
            "source_uri": dataset.source_uri,
        },
        "execution": {
            "execution_mode": request.execution_mode,
            "max_steps": request.max_steps,
            "doc_id": request.doc_id,
            "knowledge_base_id": request.knowledge_base_id,
        },
        "retrieval": {
            "retrieval_top_k": settings.retrieval_top_k,
            "sparse_retrieval_top_k": settings.sparse_retrieval_top_k,
            "rerank_top_k": settings.rerank_top_k,
            "reranker_provider": settings.reranker_provider,
        },
        "chunking": {
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
        },
        "llm": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
        },
        "embedding": {
            "provider": settings.embedding_provider,
            "model": settings.embedding_model,
            "dim": settings.embedding_dim,
        },
        "cost": {
            "currency": "USD",
            "estimated": True,
            "input_token_price_per_1k": 0.0,
            "output_token_price_per_1k": 0.0,
            "status": "placeholder",
        },
    }


def _coverage(matched_count: int, total_count: int) -> float:
    return round(matched_count / total_count, 3) if total_count else 1.0


def _mean_reciprocal_rank(
    expected_keywords: list[str],
    trace: RetrievalTraceResponse | None,
) -> float:
    if trace is None:
        return 0.0
    if not expected_keywords:
        return 1.0 if trace.evidence_pack else 0.0
    normalized_keywords = [keyword.lower() for keyword in expected_keywords]
    for rank, item in enumerate(trace.evidence_pack, start=1):
        text = item.text.lower()
        if any(keyword in text for keyword in normalized_keywords):
            return round(1 / rank, 3)
    return 0.0


def _citation_accuracy(
    *,
    answer_status: str,
    citation_count: int,
    supported_citation_count: int,
) -> float:
    if citation_count == 0:
        return 1.0 if answer_status != "answered" else 0.0
    return round(supported_citation_count / citation_count, 3)


def _citation_coverage(*, citation_count: int, evidence_count: int) -> float:
    if evidence_count == 0:
        return 1.0 if citation_count == 0 else 0.0
    return round(min(citation_count, evidence_count) / evidence_count, 3)


def _faithfulness_proxy(
    *,
    answer_status: str,
    answer_keyword_matches: list[str],
    evidence_keyword_matches: list[str],
) -> float:
    if answer_status != "answered":
        return 1.0
    if not answer_keyword_matches:
        return 0.0
    supported = set(answer_keyword_matches) & set(evidence_keyword_matches)
    return round(len(supported) / len(answer_keyword_matches), 3)


def _estimate_tokens(text: str) -> int:
    compact = text.strip()
    if not compact:
        return 0
    return max(1, round(len(compact) / 4))


def _numeric_metric(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _elapsed_ms(started_at: float) -> int:
    return max(0, round((time.perf_counter() - started_at) * 1000))


def _answer_from_retrieval(question: str, retrieval: RetrievalResult) -> ChatResult:
    from app.services.chat_service import answer_from_retrieval

    return answer_from_retrieval(question, retrieval)


def _serialize_citations(citations: list[object]) -> list[dict[str, object]]:
    serialized: list[dict[str, object]] = []
    for citation in citations:
        serialized.append(
            {
                "doc_id": getattr(citation, "doc_id", ""),
                "chunk_id": getattr(citation, "chunk_id", ""),
                "section": getattr(citation, "section", ""),
                "page": getattr(citation, "page", getattr(citation, "page_start", 0)),
                "quote": getattr(citation, "quote", getattr(citation, "text", ""))[:400],
                "score": getattr(citation, "score", 0.0),
            }
        )
    return serialized
