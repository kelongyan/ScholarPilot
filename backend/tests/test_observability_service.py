"""Tests for observability summary aggregation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace


def test_get_summary_aggregates_quality_and_backlog(monkeypatch) -> None:
    from app.services import observability_service

    now = datetime(2026, 7, 1, tzinfo=UTC)
    older_run = SimpleNamespace(
        run_id="eval-old",
        dataset_key="phase2_fixed_qa",
        dataset_version="sha256:old",
        execution_mode="chat",
        question_count=2,
        passed_count=1,
        average_latency_ms=200,
        metrics_json={
            "average_keyword_coverage": 0.5,
            "average_recall_at_k": 0.5,
            "average_citation_accuracy": 0.5,
            "average_faithfulness": 0.5,
            "average_answer_relevance": 0.5,
        },
        created_at=now - timedelta(days=1),
    )
    latest_run = SimpleNamespace(
        run_id="eval-latest",
        dataset_key="phase2_fixed_qa",
        dataset_version="sha256:latest",
        execution_mode="chat",
        question_count=2,
        passed_count=2,
        average_latency_ms=120,
        metrics_json={
            "average_keyword_coverage": 0.8,
            "average_recall_at_k": 0.75,
            "average_citation_accuracy": 1.0,
            "average_faithfulness": 0.9,
            "average_answer_relevance": 0.8,
            "answer_rate": 0.75,
            "trace_rate": 1.0,
            "error_rate": 0.0,
        },
        created_at=now,
    )
    question_logs = [
        SimpleNamespace(
            question_log_id="ql-1",
            knowledge_base_id="kb-1",
            answer_status="answered",
        ),
        SimpleNamespace(
            question_log_id="ql-2",
            knowledge_base_id="kb-1",
            answer_status="insufficient_evidence",
        ),
        SimpleNamespace(
            question_log_id="ql-3",
            knowledge_base_id="kb-2",
            answer_status="failed",
        ),
    ]
    feedback_items = [
        SimpleNamespace(question_log_id="ql-1", useful=False, citation_accurate=True),
        SimpleNamespace(question_log_id="ql-2", useful=True, citation_accurate=False),
        SimpleNamespace(question_log_id="ql-3", useful=False, citation_accurate=False),
    ]
    traces = [
        SimpleNamespace(question_log_id="ql-1", latency_ms=10),
        SimpleNamespace(question_log_id="ql-2", latency_ms=20),
        SimpleNamespace(question_log_id="ql-3", latency_ms=999),
    ]
    pending_items = [
        SimpleNamespace(item_id="item-1", severity="high", signal_count=3),
        SimpleNamespace(item_id="item-2", severity="medium", signal_count=1),
    ]

    monkeypatch.setattr(
        observability_service.evaluation_repo,
        "list_runs",
        lambda db, **kwargs: [older_run, latest_run],
    )
    monkeypatch.setattr(
        observability_service.question_log_repo,
        "list_question_logs",
        lambda db: question_logs,
    )
    monkeypatch.setattr(
        observability_service.question_log_repo,
        "list_answer_feedback",
        lambda db: feedback_items,
    )
    monkeypatch.setattr(
        observability_service.chat_trace_repo,
        "list_chat_traces",
        lambda db: traces,
    )
    monkeypatch.setattr(
        observability_service.knowledge_operation_repo,
        "list_items",
        lambda db, **kwargs: pending_items,
    )

    summary = observability_service.get_summary(object(), knowledge_base_id="kb-1")

    assert summary.latest_evaluation is not None
    assert summary.latest_evaluation.run_id == "eval-latest"
    assert summary.latest_evaluation.dataset_version == "sha256:latest"
    assert summary.latest_evaluation.pass_rate == 1.0
    assert summary.latest_evaluation.average_keyword_coverage == 0.8
    assert summary.latest_evaluation.average_recall_at_k == 0.75
    assert summary.latest_evaluation.average_citation_accuracy == 1.0
    assert summary.question_count == 2
    assert summary.answered_count == 1
    assert summary.unresolved_answer_count == 1
    assert summary.no_answer_rate == 0.5
    assert summary.feedback_count == 2
    assert summary.negative_feedback_count == 2
    assert summary.negative_feedback_rate == 1.0
    assert summary.trace_count == 2
    assert summary.average_trace_latency_ms == 15
    assert summary.pending_operation_count == 2
    assert summary.high_severity_pending_count == 1
    assert summary.operation_signal_count == 4
    assert len(summary.evaluation_trend) == 2
    assert summary.evaluation_trend[-1].run_id == "eval-latest"
    assert summary.latency_buckets[0].count == 2
    assert summary.regression_alerts == []


def test_get_summary_detects_evaluation_regression(monkeypatch) -> None:
    from app.services import observability_service

    now = datetime(2026, 7, 1, tzinfo=UTC)
    previous_run = SimpleNamespace(
        run_id="eval-previous",
        dataset_key="phase2_fixed_qa",
        dataset_version="sha256:previous",
        execution_mode="chat",
        question_count=2,
        passed_count=2,
        average_latency_ms=100,
        metrics_json={
            "average_keyword_coverage": 0.9,
            "average_recall_at_k": 0.9,
            "average_citation_accuracy": 0.9,
            "average_faithfulness": 0.9,
            "error_rate": 0.0,
        },
        created_at=now - timedelta(days=1),
    )
    current_run = SimpleNamespace(
        run_id="eval-current",
        dataset_key="phase2_fixed_qa",
        dataset_version="sha256:current",
        execution_mode="chat",
        question_count=2,
        passed_count=1,
        average_latency_ms=800,
        metrics_json={
            "average_keyword_coverage": 0.7,
            "average_recall_at_k": 0.6,
            "average_citation_accuracy": 0.7,
            "average_faithfulness": 0.7,
            "error_rate": 0.1,
        },
        created_at=now,
    )

    monkeypatch.setattr(
        observability_service.evaluation_repo,
        "list_runs",
        lambda db, **kwargs: [previous_run, current_run],
    )
    monkeypatch.setattr(
        observability_service.question_log_repo,
        "list_question_logs",
        lambda db: [],
    )
    monkeypatch.setattr(
        observability_service.question_log_repo,
        "list_answer_feedback",
        lambda db: [],
    )
    monkeypatch.setattr(
        observability_service.chat_trace_repo,
        "list_chat_traces",
        lambda db: [],
    )
    monkeypatch.setattr(
        observability_service.knowledge_operation_repo,
        "list_items",
        lambda db, **kwargs: [],
    )

    summary = observability_service.get_summary(object(), knowledge_base_id="kb-1")

    alert_metrics = {alert.metric for alert in summary.regression_alerts}
    assert "pass_rate" in alert_metrics
    assert "average_recall_at_k" in alert_metrics
    assert "average_latency_ms" in alert_metrics
    assert "error_rate" in alert_metrics


def test_get_summary_respects_allowed_kb_scope(monkeypatch) -> None:
    from app.services import observability_service

    calls: list[str | None] = []

    def fake_list_runs(db, **kwargs):
        calls.append(kwargs.get("knowledge_base_id"))
        return []

    monkeypatch.setattr(observability_service.evaluation_repo, "list_runs", fake_list_runs)
    monkeypatch.setattr(
        observability_service.question_log_repo,
        "list_question_logs",
        lambda db: [
            SimpleNamespace(
                question_log_id="ql-1",
                knowledge_base_id="kb-allowed",
                answer_status="answered",
            ),
            SimpleNamespace(
                question_log_id="ql-2",
                knowledge_base_id="kb-blocked",
                answer_status="failed",
            ),
        ],
    )
    monkeypatch.setattr(
        observability_service.question_log_repo,
        "list_answer_feedback",
        lambda db: [],
    )
    monkeypatch.setattr(
        observability_service.chat_trace_repo,
        "list_chat_traces",
        lambda db: [
            SimpleNamespace(question_log_id="ql-1", latency_ms=10),
            SimpleNamespace(question_log_id="ql-2", latency_ms=20),
        ],
    )
    monkeypatch.setattr(
        observability_service.knowledge_operation_repo,
        "list_items",
        lambda db, **kwargs: [],
    )

    summary = observability_service.get_summary(
        object(),
        allowed_knowledge_base_ids={"kb-allowed"},
    )

    assert calls == ["kb-allowed"]
    assert summary.question_count == 1
    assert summary.trace_count == 1
