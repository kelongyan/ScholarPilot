"""Observability summary schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ObservabilityEvaluationSummaryResponse(BaseModel):
    """Latest evaluation signal included in the observability summary."""

    run_id: str
    dataset_key: str
    dataset_version: str = ""
    execution_mode: str
    pass_rate: float
    average_keyword_coverage: float
    average_recall_at_k: float = 0.0
    average_mrr: float = 0.0
    average_citation_accuracy: float = 0.0
    average_faithfulness: float = 0.0
    average_answer_relevance: float = 0.0
    answer_rate: float
    trace_rate: float
    error_rate: float
    average_latency_ms: int
    created_at: datetime


class ObservabilityTrendPointResponse(ObservabilityEvaluationSummaryResponse):
    """A historical evaluation point for trend rendering."""


class ObservabilityRegressionAlertResponse(BaseModel):
    """A regression signal derived from the two latest comparable runs."""

    metric: str
    severity: str
    current_value: float
    previous_value: float
    delta: float
    message: str


class ObservabilityLatencyBucketResponse(BaseModel):
    """Trace latency bucket for lightweight distribution rendering."""

    label: str
    min_ms: int
    max_ms: int | None = None
    count: int = 0


class ObservabilitySummaryResponse(BaseModel):
    """Knowledge-base quality and operations summary."""

    knowledge_base_id: str | None = None
    latest_evaluation: ObservabilityEvaluationSummaryResponse | None = None
    evaluation_trend: list[ObservabilityTrendPointResponse] = []
    regression_alerts: list[ObservabilityRegressionAlertResponse] = []
    latency_buckets: list[ObservabilityLatencyBucketResponse] = []
    question_count: int = 0
    answered_count: int = 0
    unresolved_answer_count: int = 0
    no_answer_rate: float = 0.0
    feedback_count: int = 0
    negative_feedback_count: int = 0
    negative_feedback_rate: float = 0.0
    trace_count: int = 0
    average_trace_latency_ms: int = 0
    pending_operation_count: int = 0
    high_severity_pending_count: int = 0
    operation_signal_count: int = 0
    generated_at: datetime
