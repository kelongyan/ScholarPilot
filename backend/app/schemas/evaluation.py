"""Evaluation dataset and run schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EvaluationExecutionMode = Literal["chat", "agent"]
EvaluationRunStatus = Literal["running", "completed", "failed"]
EvaluationItemStatus = Literal["passed", "failed", "error"]


class EvaluationDatasetQuestionResponse(BaseModel):
    """A single question inside a fixed evaluation dataset."""

    sequence: int
    question: str
    expected_keywords: list[str] = Field(default_factory=list)
    notes: str = ""


class EvaluationDatasetResponse(BaseModel):
    """Public evaluation dataset representation."""

    model_config = ConfigDict(from_attributes=True)

    dataset_key: str
    name: str
    description: str
    source_uri: str
    question_count: int = 0
    created_at: datetime
    updated_at: datetime


class EvaluationDatasetDetailResponse(EvaluationDatasetResponse):
    """Evaluation dataset detail with question definitions."""

    questions: list[EvaluationDatasetQuestionResponse] = Field(default_factory=list)


class EvaluationDatasetListResponse(BaseModel):
    """List of evaluation datasets."""

    evaluation_datasets: list[EvaluationDatasetResponse]


class EvaluationRunCreateRequest(BaseModel):
    """Create and execute an evaluation run."""

    dataset_key: str = Field(default="phase2_fixed_qa")
    knowledge_base_id: str | None = None
    doc_id: str | None = None
    execution_mode: EvaluationExecutionMode = Field(default="chat")
    max_steps: int = Field(default=5, ge=3, le=8)

    @model_validator(mode="after")
    def validate_scope(self) -> EvaluationRunCreateRequest:
        if not self.knowledge_base_id and not self.doc_id:
            msg = "Either knowledge_base_id or doc_id is required."
            raise ValueError(msg)
        return self


class EvaluationRunItemResponse(BaseModel):
    """A single evaluated question result."""

    model_config = ConfigDict(from_attributes=True)

    item_id: str
    sequence: int
    question: str
    expected_keywords: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    metrics_json: dict[str, object] = Field(default_factory=dict)
    answer: str
    answer_status: str
    execution_route: str
    status: EvaluationItemStatus
    error_message: str = ""
    latency_ms: int = 0
    question_log_id: str | None = None
    chat_trace_id: str | None = None
    agent_run_id: str | None = None
    created_at: datetime


class EvaluationRunResponse(BaseModel):
    """A persisted evaluation run."""

    run_id: str
    dataset_key: str
    dataset_name: str
    knowledge_base_id: str | None = None
    doc_id: str | None = None
    execution_mode: EvaluationExecutionMode
    status: EvaluationRunStatus
    question_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    average_latency_ms: int = 0
    dataset_version: str = ""
    config_snapshot_json: dict[str, object] = Field(default_factory=dict)
    pass_rate: float = 0.0
    summary_json: dict[str, object] = Field(default_factory=dict)
    metrics_json: dict[str, object] = Field(default_factory=dict)
    previous_run_id: str | None = None
    metric_deltas: dict[str, float] = Field(default_factory=dict)
    items: list[EvaluationRunItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class EvaluationRunListResponse(BaseModel):
    """List of persisted evaluation runs."""

    evaluation_runs: list[EvaluationRunResponse]
