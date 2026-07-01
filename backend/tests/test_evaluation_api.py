"""Tests for evaluation API routes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app

client = TestClient(app)


class _FakeDataset:
    dataset_key = "phase2_fixed_qa"
    name = "Phase 2 fixed QA set"
    description = "Repeatable evaluation set"
    source_uri = "tests/fixtures/phase2_eval_questions.csv"
    questions_json = [
        {
            "sequence": 1,
            "question": "What retrieval pipeline is used for answering questions?",
            "expected_keywords": ["rewrite", "BM25", "dense"],
            "notes": "Should mention hybrid retrieval pipeline stages",
        }
    ]
    created_at = datetime(2026, 6, 30, tzinfo=UTC)
    updated_at = datetime(2026, 6, 30, tzinfo=UTC)


class _FakeRun:
    run_id = "eval-run-1"
    dataset_key = "phase2_fixed_qa"
    knowledge_base_id = "kb-1"
    doc_id = None
    execution_mode = "chat"
    status = "completed"
    question_count = 1
    passed_count = 1
    failed_count = 0
    average_latency_ms = 11
    summary_json = {"pass_rate": 1.0}
    metrics_json = {"average_keyword_coverage": 1.0, "answer_rate": 1.0}
    created_at = datetime(2026, 6, 30, tzinfo=UTC)
    updated_at = datetime(2026, 6, 30, tzinfo=UTC)


class _FakeRunItem:
    item_id = "eval-item-1"
    sequence = 1
    question = "What retrieval pipeline is used for answering questions?"
    expected_keywords_json = ["rewrite", "BM25", "dense"]
    matched_keywords_json = ["rewrite", "BM25", "dense"]
    missing_keywords_json = []
    metrics_json = {"keyword_coverage": 1.0}
    answer = "Hybrid retrieval uses rewrite, dense, and BM25."
    answer_status = "answered"
    execution_route = "chat"
    status = "passed"
    error_message = ""
    latency_ms = 11
    question_log_id = "ql-1"
    chat_trace_id = "trace-1"
    agent_run_id = None
    created_at = datetime(2026, 6, 30, tzinfo=UTC)


def _fake_get_db():
    yield object()


def test_list_evaluation_datasets(monkeypatch) -> None:
    from app.services import evaluation_service

    monkeypatch.setattr(evaluation_service, "_ensure_phase2_dataset", lambda db: _FakeDataset())
    monkeypatch.setattr(
        evaluation_service.evaluation_repo, "list_datasets", lambda db: [_FakeDataset()]
    )

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get("/evaluations/datasets")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    body = response.json()
    assert body["evaluation_datasets"][0]["dataset_key"] == "phase2_fixed_qa"
    assert body["evaluation_datasets"][0]["question_count"] == 1


def test_create_evaluation_run(monkeypatch) -> None:
    from app.repositories import knowledge_base_repo
    from app.services import audit_log_service, evaluation_service

    captured = {}

    class FakeKnowledgeBase:
        knowledge_base_id = "kb-1"

    def fake_try_log_event(db, **kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr(
        knowledge_base_repo,
        "get_knowledge_base",
        lambda db, knowledge_base_id: FakeKnowledgeBase(),
    )
    monkeypatch.setattr(evaluation_service, "run_evaluation", lambda db, request: _run_response())
    monkeypatch.setattr(audit_log_service, "try_log_event", fake_try_log_event)

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.post(
            "/evaluations/runs",
            json={
                "dataset_key": "phase2_fixed_qa",
                "knowledge_base_id": "kb-1",
                "execution_mode": "chat",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 201
    assert response.json()["run_id"] == "eval-run-1"
    assert captured["action"] == "evaluation_run.created"
    assert captured["resource_type"] == "evaluation_run"
    assert captured["resource_id"] == "eval-run-1"
    assert captured["knowledge_base_id"] == "kb-1"
    assert captured["detail_json"]["dataset_key"] == "phase2_fixed_qa"


def test_create_evaluation_run_rejects_non_indexed_document(monkeypatch) -> None:
    from app.repositories import document_repo

    class FakeDoc:
        status = "indexing"
        knowledge_base_id = "kb-1"

    monkeypatch.setattr(document_repo, "get_document", lambda db, doc_id: FakeDoc())

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.post(
            "/evaluations/runs",
            json={
                "dataset_key": "phase2_fixed_qa",
                "doc_id": "doc-1",
                "execution_mode": "chat",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 409


def test_get_evaluation_run(monkeypatch) -> None:
    from app.services import evaluation_service

    monkeypatch.setattr(evaluation_service, "get_run_response", lambda db, run_id: _run_response())

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get("/evaluations/runs/eval-run-1")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["items"][0]["item_id"] == "eval-item-1"


def test_list_evaluation_runs(monkeypatch) -> None:
    from app.services import evaluation_service

    captured = {}

    def fake_list_runs(db, **kwargs):
        captured.update(kwargs)
        return [_run_response()]

    monkeypatch.setattr(evaluation_service, "list_runs", fake_list_runs)

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get(
            "/evaluations/runs",
            params={
                "dataset_key": "phase2_fixed_qa",
                "knowledge_base_id": "kb-1",
                "execution_mode": "chat",
                "status": "completed",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["evaluation_runs"][0]["run_id"] == "eval-run-1"
    assert response.json()["evaluation_runs"][0]["metric_deltas"] == {}
    assert captured["dataset_key"] == "phase2_fixed_qa"
    assert captured["knowledge_base_id"] == "kb-1"
    assert captured["execution_mode"] == "chat"
    assert captured["status"] == "completed"


def _run_response():
    from app.schemas.evaluation import EvaluationRunItemResponse, EvaluationRunResponse

    return EvaluationRunResponse(
        run_id="eval-run-1",
        dataset_key="phase2_fixed_qa",
        dataset_name="Phase 2 fixed QA set",
        knowledge_base_id="kb-1",
        doc_id=None,
        execution_mode="chat",
        status="completed",
        question_count=1,
        passed_count=1,
        failed_count=0,
        average_latency_ms=11,
        pass_rate=1.0,
        summary_json={"pass_rate": 1.0},
        metrics_json={"average_keyword_coverage": 1.0, "answer_rate": 1.0},
        items=[
            EvaluationRunItemResponse(
                item_id="eval-item-1",
                sequence=1,
                question="What retrieval pipeline is used for answering questions?",
                expected_keywords=["rewrite", "BM25", "dense"],
                matched_keywords=["rewrite", "BM25", "dense"],
                missing_keywords=[],
                metrics_json={"keyword_coverage": 1.0},
                answer="Hybrid retrieval uses rewrite, dense, and BM25.",
                answer_status="answered",
                execution_route="chat",
                status="passed",
                error_message="",
                latency_ms=11,
                question_log_id="ql-1",
                chat_trace_id="trace-1",
                agent_run_id=None,
                created_at=datetime(2026, 6, 30, tzinfo=UTC),
            )
        ],
        created_at=datetime(2026, 6, 30, tzinfo=UTC),
        updated_at=datetime(2026, 6, 30, tzinfo=UTC),
    )
