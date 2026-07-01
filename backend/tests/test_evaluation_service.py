"""Tests for the repeatable evaluation service."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services import evaluation_service


def test_phase2_eval_question_set_is_repeatable() -> None:
    questions = evaluation_service.load_phase2_eval_questions()

    assert len(questions) >= 3
    assert questions[0]["question"]
    assert "expected_keywords" in questions[0]


def test_list_datasets_seeds_default_dataset(monkeypatch) -> None:
    class FakeDataset:
        dataset_key = "phase2_fixed_qa"
        name = "Phase 2 fixed QA set"
        description = "Repeatable evaluation set"
        source_uri = "tests/fixtures/phase2_eval_questions.csv"
        questions_json = [{"sequence": 1, "question": "Q", "expected_keywords": ["a"]}]
        created_at = datetime(2026, 6, 30, tzinfo=UTC)
        updated_at = datetime(2026, 6, 30, tzinfo=UTC)

    monkeypatch.setattr(
        evaluation_service.evaluation_repo, "list_datasets", lambda db: [FakeDataset()]
    )
    monkeypatch.setattr(evaluation_service, "_ensure_phase2_dataset", lambda db: FakeDataset())

    datasets = evaluation_service.list_datasets(object())

    assert datasets[0].dataset_key == "phase2_fixed_qa"
    assert datasets[0].question_count == 1


def test_get_dataset_detail_returns_questions(monkeypatch) -> None:
    class FakeDataset:
        dataset_key = "phase2_fixed_qa"
        name = "Phase 2 fixed QA set"
        description = "Repeatable evaluation set"
        source_uri = "tests/fixtures/phase2_eval_questions.csv"
        questions_json = [
            {"sequence": 1, "question": "Q", "expected_keywords": ["a"], "notes": "note"}
        ]
        created_at = datetime(2026, 6, 30, tzinfo=UTC)
        updated_at = datetime(2026, 6, 30, tzinfo=UTC)

    monkeypatch.setattr(evaluation_service, "_ensure_phase2_dataset", lambda db: FakeDataset())
    monkeypatch.setattr(
        evaluation_service.evaluation_repo, "get_dataset", lambda db, key: FakeDataset()
    )

    dataset = evaluation_service.get_dataset_detail(object(), "phase2_fixed_qa")

    assert dataset is not None
    assert dataset.questions[0].question == "Q"


def test_evaluation_metrics_calculate_quality_observability() -> None:
    from app.schemas.rag import EvidenceItemResponse, RetrievalTraceResponse

    trace = RetrievalTraceResponse(
        query="How does retrieval work?",
        rewritten_query="retrieval",
        evidence_pack=[
            EvidenceItemResponse(
                doc_id="doc-1",
                chunk_id="chunk-1",
                section="retrieval",
                page_start=1,
                page_end=1,
                score=0.9,
                retrieval_source="rerank",
                text="Hybrid retrieval uses rewrite and BM25 lexical matching.",
            )
        ],
    )
    item_metrics = evaluation_service._item_metrics(
        question="How does retrieval work?",
        expected_keywords=["rewrite", "bm25"],
        matched_keywords=["rewrite"],
        answer="Hybrid retrieval uses rewrite.",
        answer_status="answered",
        trace=trace,
        trace_blob="trace",
        citations_json=[{"chunk_id": "chunk-1"}],
        latency_ms=25,
        error_message="",
    )
    run_metrics = evaluation_service._run_metrics([item_metrics], 25, 1)

    assert item_metrics["keyword_coverage"] == 0.5
    assert item_metrics["has_answer"] is True
    assert item_metrics["has_trace"] is True
    assert item_metrics["recall_at_k"] == 1.0
    assert item_metrics["mrr"] == 1.0
    assert item_metrics["citation_accuracy"] == 1.0
    assert item_metrics["faithfulness"] == 1.0
    assert item_metrics["estimated_total_tokens"] > 0
    assert run_metrics["average_keyword_coverage"] == 0.5
    assert run_metrics["average_recall_at_k"] == 1.0
    assert run_metrics["average_citation_accuracy"] == 1.0
    assert run_metrics["answer_rate"] == 1.0
    assert run_metrics["trace_rate"] == 1.0


def test_dataset_version_and_config_snapshot_are_stable() -> None:
    class FakeDataset:
        dataset_key = "phase2_fixed_qa"
        source_uri = "tests/fixtures/phase2_eval_questions.csv"
        questions_json = [{"sequence": 1, "question": "Q", "expected_keywords": ["a"]}]

    request = evaluation_service.EvaluationRunCreateRequest(
        dataset_key="phase2_fixed_qa",
        knowledge_base_id="kb-1",
        execution_mode="chat",
    )

    version = evaluation_service._dataset_version(FakeDataset())
    snapshot = evaluation_service._config_snapshot(
        request=request,
        dataset=FakeDataset(),
        dataset_version=version,
    )

    assert version.startswith("sha256:")
    assert evaluation_service._dataset_version(FakeDataset()) == version
    assert snapshot["dataset"]["dataset_version"] == version
    assert snapshot["retrieval"]["reranker_provider"]
    assert snapshot["cost"]["status"] == "placeholder"


def test_evaluation_metric_deltas_compare_previous_run() -> None:
    class CurrentRun:
        passed_count = 2
        question_count = 4
        average_latency_ms = 120
        metrics_json = {
            "average_keyword_coverage": 0.75,
            "average_recall_at_k": 0.75,
            "average_citation_accuracy": 1.0,
            "average_faithfulness": 0.8,
            "answer_rate": 1.0,
            "trace_rate": 1.0,
            "error_rate": 0.0,
            "average_answer_length": 80,
            "max_latency_ms": 200,
        }

    class PreviousRun:
        passed_count = 1
        question_count = 4
        average_latency_ms = 150
        metrics_json = {
            "average_keyword_coverage": 0.5,
            "average_recall_at_k": 0.5,
            "average_citation_accuracy": 0.5,
            "average_faithfulness": 0.6,
            "answer_rate": 0.75,
            "trace_rate": 1.0,
            "error_rate": 0.25,
            "average_answer_length": 60,
            "max_latency_ms": 250,
        }

    deltas = evaluation_service._metric_deltas(CurrentRun(), PreviousRun(), 0.5)

    assert deltas["pass_rate"] == 0.25
    assert deltas["average_keyword_coverage"] == 0.25
    assert deltas["average_recall_at_k"] == 0.25
    assert deltas["average_citation_accuracy"] == 0.5
    assert deltas["average_faithfulness"] == 0.2
    assert deltas["answer_rate"] == 0.25
    assert deltas["error_rate"] == -0.25
    assert deltas["average_latency_ms"] == -30
