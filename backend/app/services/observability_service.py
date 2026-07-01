"""Aggregate quality and operations signals for lightweight observability."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.repositories import (
    chat_trace_repo,
    evaluation_repo,
    knowledge_operation_repo,
    question_log_repo,
)
from app.schemas.observability import (
    ObservabilityEvaluationSummaryResponse,
    ObservabilityLatencyBucketResponse,
    ObservabilityRegressionAlertResponse,
    ObservabilitySummaryResponse,
    ObservabilityTrendPointResponse,
)


def get_summary(
    db: Session,
    *,
    knowledge_base_id: str | None = None,
    allowed_knowledge_base_ids: Iterable[str] | None = None,
) -> ObservabilitySummaryResponse:
    """Build a current quality summary from persisted traces, evals, and operations."""
    allowed_ids = (
        frozenset(str(item) for item in allowed_knowledge_base_ids)
        if allowed_knowledge_base_ids is not None
        else None
    )
    runs = _list_completed_runs(
        db,
        knowledge_base_id=knowledge_base_id,
        allowed_knowledge_base_ids=allowed_ids,
    )
    latest_run = _latest_by_created_at(runs)
    sorted_runs = sorted(runs, key=_created_at_sort_key, reverse=True)
    previous_run = sorted_runs[1] if len(sorted_runs) > 1 else None
    question_logs = [
        log
        for log in question_log_repo.list_question_logs(db)
        if _matches_scope(
            getattr(log, "knowledge_base_id", None),
            knowledge_base_id,
            allowed_ids,
        )
    ]
    question_log_ids = {str(log.question_log_id) for log in question_logs}
    feedback_items = [
        feedback
        for feedback in question_log_repo.list_answer_feedback(db)
        if str(feedback.question_log_id) in question_log_ids
    ]
    traces = [
        trace
        for trace in chat_trace_repo.list_chat_traces(db)
        if str(trace.question_log_id) in question_log_ids
    ]
    pending_items = _list_pending_operation_items(
        db,
        knowledge_base_id=knowledge_base_id,
        allowed_knowledge_base_ids=allowed_ids,
    )

    question_count = len(question_logs)
    answered_count = sum(1 for log in question_logs if log.answer_status == "answered")
    unresolved_answer_count = max(0, question_count - answered_count)
    feedback_count = len(feedback_items)
    negative_feedback_count = sum(
        1
        for feedback in feedback_items
        if getattr(feedback, "useful", None) is False
        or getattr(feedback, "citation_accurate", None) is False
    )
    trace_latencies = [int(getattr(trace, "latency_ms", 0) or 0) for trace in traces]

    return ObservabilitySummaryResponse(
        knowledge_base_id=knowledge_base_id,
        latest_evaluation=_evaluation_summary(latest_run),
        evaluation_trend=_evaluation_trend(sorted_runs),
        regression_alerts=_regression_alerts(latest_run, previous_run),
        question_count=question_count,
        answered_count=answered_count,
        unresolved_answer_count=unresolved_answer_count,
        no_answer_rate=_rate(unresolved_answer_count, question_count),
        feedback_count=feedback_count,
        negative_feedback_count=negative_feedback_count,
        negative_feedback_rate=_rate(negative_feedback_count, feedback_count),
        trace_count=len(traces),
        average_trace_latency_ms=(
            round(sum(trace_latencies) / len(trace_latencies)) if trace_latencies else 0
        ),
        latency_buckets=_latency_buckets(trace_latencies),
        pending_operation_count=len(pending_items),
        high_severity_pending_count=sum(
            1
            for item in pending_items
            if str(getattr(item, "severity", "")).lower() in {"high", "critical"}
        ),
        operation_signal_count=sum(
            int(getattr(item, "signal_count", 1) or 1) for item in pending_items
        ),
        generated_at=datetime.now(UTC),
    )


def _list_completed_runs(
    db: Session,
    *,
    knowledge_base_id: str | None,
    allowed_knowledge_base_ids: frozenset[str] | None,
) -> list[Any]:
    if knowledge_base_id is not None or allowed_knowledge_base_ids is None:
        return evaluation_repo.list_runs(
            db,
            knowledge_base_id=knowledge_base_id,
            status="completed",
        )
    runs_by_id: dict[str, Any] = {}
    for allowed_id in sorted(allowed_knowledge_base_ids):
        for run in evaluation_repo.list_runs(
            db,
            knowledge_base_id=allowed_id,
            status="completed",
        ):
            runs_by_id[str(run.run_id)] = run
    return list(runs_by_id.values())


def _list_pending_operation_items(
    db: Session,
    *,
    knowledge_base_id: str | None,
    allowed_knowledge_base_ids: frozenset[str] | None,
) -> list[Any]:
    if knowledge_base_id is not None or allowed_knowledge_base_ids is None:
        return knowledge_operation_repo.list_items(
            db,
            knowledge_base_id=knowledge_base_id,
            status="pending",
        )
    items_by_id: dict[str, Any] = {}
    for allowed_id in sorted(allowed_knowledge_base_ids):
        for item in knowledge_operation_repo.list_items(
            db,
            knowledge_base_id=allowed_id,
            status="pending",
        ):
            items_by_id[str(item.item_id)] = item
    return list(items_by_id.values())


def _latest_by_created_at(items: list[Any]) -> Any | None:
    if not items:
        return None
    return max(items, key=_created_at_sort_key)


def _created_at_sort_key(item: Any) -> datetime:
    value = getattr(item, "created_at", None)
    if isinstance(value, datetime):
        return value
    return datetime.min


def _evaluation_summary(run: Any | None) -> ObservabilityEvaluationSummaryResponse | None:
    if run is None:
        return None
    metrics = getattr(run, "metrics_json", {}) or {}
    question_count = int(getattr(run, "question_count", 0) or 0)
    passed_count = int(getattr(run, "passed_count", 0) or 0)
    pass_rate = round(passed_count / question_count, 3) if question_count else 0.0
    return ObservabilityEvaluationSummaryResponse(
        run_id=str(run.run_id),
        dataset_key=str(run.dataset_key),
        dataset_version=str(getattr(run, "dataset_version", "") or ""),
        execution_mode=str(run.execution_mode),
        pass_rate=pass_rate,
        average_keyword_coverage=_numeric_metric(metrics.get("average_keyword_coverage")),
        average_recall_at_k=_numeric_metric(metrics.get("average_recall_at_k")),
        average_mrr=_numeric_metric(metrics.get("average_mrr")),
        average_citation_accuracy=_numeric_metric(
            metrics.get("average_citation_accuracy")
        ),
        average_faithfulness=_numeric_metric(metrics.get("average_faithfulness")),
        average_answer_relevance=_numeric_metric(metrics.get("average_answer_relevance")),
        answer_rate=_numeric_metric(metrics.get("answer_rate")),
        trace_rate=_numeric_metric(metrics.get("trace_rate")),
        error_rate=_numeric_metric(metrics.get("error_rate")),
        average_latency_ms=int(getattr(run, "average_latency_ms", 0) or 0),
        created_at=run.created_at,
    )


def _evaluation_trend(
    runs_desc: list[Any],
    *,
    limit: int = 5,
) -> list[ObservabilityTrendPointResponse]:
    points: list[ObservabilityTrendPointResponse] = []
    for run in reversed(runs_desc[:limit]):
        summary = _evaluation_summary(run)
        if summary is not None:
            points.append(ObservabilityTrendPointResponse(**summary.model_dump()))
    return points


def _regression_alerts(
    current_run: Any | None,
    previous_run: Any | None,
) -> list[ObservabilityRegressionAlertResponse]:
    if current_run is None or previous_run is None:
        return []

    current = _evaluation_summary(current_run)
    previous = _evaluation_summary(previous_run)
    if current is None or previous is None:
        return []

    checks = [
        ("pass_rate", current.pass_rate, previous.pass_rate, -0.05, "high"),
        (
            "average_keyword_coverage",
            current.average_keyword_coverage,
            previous.average_keyword_coverage,
            -0.1,
            "medium",
        ),
        (
            "average_recall_at_k",
            current.average_recall_at_k,
            previous.average_recall_at_k,
            -0.1,
            "medium",
        ),
        (
            "average_citation_accuracy",
            current.average_citation_accuracy,
            previous.average_citation_accuracy,
            -0.1,
            "medium",
        ),
        (
            "average_faithfulness",
            current.average_faithfulness,
            previous.average_faithfulness,
            -0.1,
            "medium",
        ),
    ]
    alerts: list[ObservabilityRegressionAlertResponse] = []
    for metric, current_value, previous_value, threshold, severity in checks:
        delta = round(current_value - previous_value, 3)
        if delta <= threshold:
            alerts.append(
                ObservabilityRegressionAlertResponse(
                    metric=metric,
                    severity=severity,
                    current_value=current_value,
                    previous_value=previous_value,
                    delta=delta,
                    message=f"{metric} regressed by {abs(delta):.3f}",
                )
            )

    latency_delta = current.average_latency_ms - previous.average_latency_ms
    if latency_delta >= max(500, round(previous.average_latency_ms * 0.25)):
        alerts.append(
            ObservabilityRegressionAlertResponse(
                metric="average_latency_ms",
                severity="medium",
                current_value=float(current.average_latency_ms),
                previous_value=float(previous.average_latency_ms),
                delta=float(latency_delta),
                message=f"average_latency_ms increased by {latency_delta}ms",
            )
        )
    if current.error_rate - previous.error_rate >= 0.05:
        delta = round(current.error_rate - previous.error_rate, 3)
        alerts.append(
            ObservabilityRegressionAlertResponse(
                metric="error_rate",
                severity="high",
                current_value=current.error_rate,
                previous_value=previous.error_rate,
                delta=delta,
                message=f"error_rate increased by {delta:.3f}",
            )
        )
    return alerts


def _latency_buckets(latencies: list[int]) -> list[ObservabilityLatencyBucketResponse]:
    buckets = [
        ObservabilityLatencyBucketResponse(label="0-250ms", min_ms=0, max_ms=250),
        ObservabilityLatencyBucketResponse(label="250ms-1s", min_ms=251, max_ms=1000),
        ObservabilityLatencyBucketResponse(label="1-3s", min_ms=1001, max_ms=3000),
        ObservabilityLatencyBucketResponse(label=">3s", min_ms=3001, max_ms=None),
    ]
    for latency in latencies:
        if latency <= 250:
            buckets[0].count += 1
        elif latency <= 1000:
            buckets[1].count += 1
        elif latency <= 3000:
            buckets[2].count += 1
        else:
            buckets[3].count += 1
    return buckets


def _matches_scope(
    item_knowledge_base_id: str | None,
    knowledge_base_id: str | None,
    allowed_knowledge_base_ids: frozenset[str] | None,
) -> bool:
    if knowledge_base_id is not None:
        return item_knowledge_base_id == knowledge_base_id
    if allowed_knowledge_base_ids is not None:
        return item_knowledge_base_id in allowed_knowledge_base_ids
    return True


def _numeric_metric(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _rate(count: int, total: int) -> float:
    return round(count / total, 3) if total else 0.0
