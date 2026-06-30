"""Chat trace schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatTraceResponse(BaseModel):
    """Public persisted trace representation."""

    model_config = ConfigDict(from_attributes=True)

    trace_id: str
    question_log_id: str
    query: str
    rewritten_query: str
    dense_results_json: list[dict[str, object]] = []
    sparse_results_json: list[dict[str, object]] = []
    fused_results_json: list[dict[str, object]] = []
    reranked_results_json: list[dict[str, object]] = []
    evidence_pack_json: list[dict[str, object]] = []
    answer: str
    citations_json: list[dict[str, object]] = []
    answer_status: str
    model: str = ""
    latency_ms: int = 0
    created_at: datetime
    updated_at: datetime


class ChatTraceListResponse(BaseModel):
    """List of persisted chat traces."""

    chat_traces: list[ChatTraceResponse]
