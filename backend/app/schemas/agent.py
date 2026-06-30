"""Schemas for controlled Phase 5 Agent runs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.chat import CitationResponse
from app.schemas.rag import RetrievalTraceResponse

AgentMode = Literal["auto", "short", "multi_agent"]


class AgentRunRequest(BaseModel):
    """A controlled Agent workflow request."""

    doc_id: str | None = Field(default=None, description="Optional document scope.")
    knowledge_base_id: str | None = Field(
        default=None, description="Optional knowledge base scope."
    )
    question: str = Field(..., min_length=1)
    mode: AgentMode = Field(
        default="auto",
        description="auto chooses short or multi_agent based on question complexity.",
    )
    max_steps: int = Field(
        default=5,
        ge=3,
        le=8,
        description="Maximum Agent steps, including the planner step.",
    )

    @model_validator(mode="after")
    def validate_scope(self) -> AgentRunRequest:
        if not self.doc_id and not self.knowledge_base_id:
            msg = "Either doc_id or knowledge_base_id is required."
            raise ValueError(msg)
        return self


class AgentStepResponse(BaseModel):
    """A single controlled Agent step with trace data."""

    sequence: int
    agent_name: str
    status: str
    input_json: dict[str, object] = Field(default_factory=dict)
    output_json: dict[str, object] = Field(default_factory=dict)
    latency_ms: int = 0
    error_message: str = ""


class AgentRunResponse(BaseModel):
    """A completed or failed Agent workflow run."""

    run_id: str
    route: str
    status: str
    doc_id: str | None = None
    knowledge_base_id: str | None = None
    question: str
    answer: str
    answer_status: str
    citations: list[CitationResponse] = Field(default_factory=list)
    trace: RetrievalTraceResponse | None = None
    agent_steps: list[AgentStepResponse] = Field(default_factory=list)
    question_log_id: str | None = None
    chat_trace_id: str | None = None
    total_latency_ms: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AgentRunListResponse(BaseModel):
    """A list of persisted Agent runs."""

    agent_runs: list[AgentRunResponse]
