"""Tests for persisted knowledge operation items."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from app.services import knowledge_operations_service


class _QuestionLog:
    question_log_id = "ql-1"
    doc_id = "doc-1"
    knowledge_base_id = "kb-1"
    question = "How do we handle incident escalation?"
    answer_status = "insufficient_evidence"
    created_at = datetime(2026, 6, 30, tzinfo=UTC)


class _AnsweredQuestionLog:
    question_log_id = "ql-2"
    doc_id = "doc-2"
    knowledge_base_id = "kb-1"
    question = "What is the owner assignment policy?"
    answer_status = "answered"
    created_at = datetime(2026, 6, 30, tzinfo=UTC)


class _DuplicateQuestionLog:
    question_log_id = "ql-duplicate"
    doc_id = "doc-1"
    knowledge_base_id = "kb-1"
    question = "How do we handle incident escalation?"
    answer_status = "insufficient_evidence"
    created_at = datetime(2026, 6, 30, 1, tzinfo=UTC)


class _Feedback:
    feedback_id = "fb-1"
    question_log_id = "ql-2"
    useful = False
    citation_accurate = False
    created_at = datetime(2026, 6, 30, tzinfo=UTC)


class _FailedDocument:
    doc_id = "doc-3"
    knowledge_base_id = "kb-1"
    title = "Broken source"
    status = "failed"
    error_message = "parse error"
    updated_at = datetime(2026, 6, 30, tzinfo=UTC)


class _AgentRun:
    run_id = "run-1"
    doc_id = "doc-1"
    knowledge_base_id = "kb-1"
    question_log_id = "ql-1"
    question = "Compare the risks and recommend the next operational steps."
    route = "multi_agent"
    status = "completed"
    answer_status = "answered"
    answer = "Answer"
    citations_json = []
    trace_json = {}
    total_latency_ms = 123


class _ReviewerStep:
    agent_name = "reviewer_agent"

    def __init__(self, *, review_status: str = "warning", unsupported_citation_count: int = 2):
        self.output_json = {
            "review_status": review_status,
            "unsupported_citation_count": unsupported_citation_count,
        }


class _PlainStep:
    agent_name = "writer_agent"
    output_json = {}


class _OperationItem:
    item_id = "item-1"
    knowledge_base_id = "kb-1"
    doc_id = "doc-1"
    question_log_id = None
    agent_run_id = None
    source_type = "document"
    source_id = "doc-1"
    suggestion_type = "reindex_document"
    aggregate_key = "kb-1|reindex_document|document|doc-1"
    signal_count = 1
    last_signal_at = datetime(2026, 6, 30, tzinfo=UTC)
    severity = "high"
    title = "Fix failed document processing"
    description = "A source document failed parsing, embedding, or indexing."
    suggested_action = "Inspect the error and reindex the document."
    status = "pending"
    resolution_note = ""


def test_list_items_syncs_generated_operations(monkeypatch) -> None:
    from app.repositories import (
        document_repo,
        knowledge_operation_repo,
        question_log_repo,
    )

    created = []
    events = []

    def fake_create_item(db, item):
        item.created_at = datetime(2026, 6, 30, tzinfo=UTC)
        item.updated_at = datetime(2026, 6, 30, tzinfo=UTC)
        created.append(item)
        return item

    def fake_create_event(db, event, *, commit=True):
        events.append(event)
        return event

    monkeypatch.setattr(
        question_log_repo,
        "list_question_logs",
        lambda db: [_QuestionLog(), _AnsweredQuestionLog()],
    )
    monkeypatch.setattr(question_log_repo, "list_answer_feedback", lambda db: [_Feedback()])
    monkeypatch.setattr(document_repo, "list_documents", lambda db: [_FailedDocument()])
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_event_by_source",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_item_by_source",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_pending_item_by_aggregate_key",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(knowledge_operation_repo, "create_item", fake_create_item)
    monkeypatch.setattr(knowledge_operation_repo, "create_event", fake_create_event)
    monkeypatch.setattr(
        knowledge_operation_repo,
        "list_items",
        lambda db, **kwargs: created,
    )

    items = knowledge_operations_service.list_items(
        SimpleNamespace(commit=lambda: None),
        knowledge_base_id="kb-1",
    )

    assert {item.suggestion_type for item in items} == {
        "faq_draft",
        "answer_quality_review",
        "reindex_document",
    }
    assert all(item.status == "pending" for item in items)
    assert len(events) == 3


def test_list_items_does_not_duplicate_existing_operations(monkeypatch) -> None:
    from app.repositories import (
        document_repo,
        knowledge_operation_repo,
        question_log_repo,
    )

    monkeypatch.setattr(question_log_repo, "list_question_logs", lambda db: [_QuestionLog()])
    monkeypatch.setattr(question_log_repo, "list_answer_feedback", lambda db: [])
    monkeypatch.setattr(document_repo, "list_documents", lambda db: [])
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_event_by_source",
        lambda db, **kwargs: SimpleNamespace(item_id="existing-item"),
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_item",
        lambda db, item_id: object(),
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_item_by_source",
        lambda db, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected source lookup")),
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_pending_item_by_aggregate_key",
        lambda db, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected aggregate lookup")),
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "create_item",
        lambda db, item: (_ for _ in ()).throw(AssertionError("unexpected create")),
    )
    monkeypatch.setattr(knowledge_operation_repo, "list_items", lambda db, **kwargs: [])

    items = knowledge_operations_service.list_items(object(), knowledge_base_id="kb-1")

    assert items == []


def test_list_items_aggregates_repeated_question_signals(monkeypatch) -> None:
    from app.repositories import (
        agent_run_repo,
        document_repo,
        knowledge_operation_repo,
        question_log_repo,
    )

    created = []
    events = []

    def fake_create_item(db, item):
        item.created_at = datetime(2026, 6, 30, tzinfo=UTC)
        item.updated_at = datetime(2026, 6, 30, tzinfo=UTC)
        created.append(item)
        return item

    def fake_create_event(db, event, *, commit=True):
        events.append(event)
        return event

    def fake_get_pending_item_by_aggregate_key(db, *, aggregate_key):
        return created[0] if created else None

    def fake_commit():
        return None

    monkeypatch.setattr(
        question_log_repo,
        "list_question_logs",
        lambda db: [_QuestionLog(), _DuplicateQuestionLog()],
    )
    monkeypatch.setattr(question_log_repo, "list_answer_feedback", lambda db: [])
    monkeypatch.setattr(document_repo, "list_documents", lambda db: [])
    monkeypatch.setattr(agent_run_repo, "list_agent_runs", lambda db, **kwargs: [])
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_event_by_source",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_event_by_source",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_item_by_source",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_pending_item_by_aggregate_key",
        fake_get_pending_item_by_aggregate_key,
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_pending_item_by_aggregate_key",
        fake_get_pending_item_by_aggregate_key,
    )
    monkeypatch.setattr(knowledge_operation_repo, "create_item", fake_create_item)
    monkeypatch.setattr(knowledge_operation_repo, "create_event", fake_create_event)
    monkeypatch.setattr(
        knowledge_operation_repo,
        "list_items",
        lambda db, **kwargs: created,
    )

    db = SimpleNamespace(commit=fake_commit)
    items = knowledge_operations_service.list_items(db, knowledge_base_id="kb-1")

    assert len(created) == 1
    assert len(events) == 2
    assert items[0].signal_count == 2
    assert items[0].aggregate_key == "kb-1|faq_draft|question|how do we handle incident escalation?"


def test_sync_agent_run_item_creates_review_item(monkeypatch) -> None:
    from app.repositories import agent_run_repo, knowledge_operation_repo

    created = []

    def fake_create_item(db, item):
        created.append(item)
        return item

    monkeypatch.setattr(agent_run_repo, "get_agent_run", lambda db, run_id: _AgentRun())
    monkeypatch.setattr(
        agent_run_repo,
        "list_agent_steps",
        lambda db, run_id: [_PlainStep(), _ReviewerStep()],
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_item_by_source",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_event_by_source",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_pending_item_by_aggregate_key",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(knowledge_operation_repo, "create_item", fake_create_item)
    monkeypatch.setattr(
        knowledge_operation_repo,
        "create_event",
        lambda db, event, *, commit=True: event,
    )

    item = knowledge_operations_service.sync_agent_run_item(
        SimpleNamespace(commit=lambda: None),
        run_id="run-1",
    )

    assert item is not None
    assert item.source_type == "agent_run"
    assert item.source_id == "run-1"
    assert item.agent_run_id == "run-1"
    assert item.suggestion_type == "agent_review"
    assert item.title == "Review Agent citation warning"
    assert created[0].agent_run_id == "run-1"


def test_sync_agent_run_item_reuses_existing_review_item(monkeypatch) -> None:
    from app.repositories import agent_run_repo, knowledge_operation_repo

    existing = object()

    monkeypatch.setattr(agent_run_repo, "get_agent_run", lambda db, run_id: _AgentRun())
    monkeypatch.setattr(
        agent_run_repo,
        "list_agent_steps",
        lambda db, run_id: [_ReviewerStep(review_status="warning", unsupported_citation_count=1)],
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_event_by_source",
        lambda db, **kwargs: SimpleNamespace(item_id="existing-item"),
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_item",
        lambda db, item_id: existing,
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_item_by_source",
        lambda db, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected source lookup")),
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "create_item",
        lambda db, item: (_ for _ in ()).throw(AssertionError("unexpected create")),
    )

    item = knowledge_operations_service.sync_agent_run_item(object(), run_id="run-1")

    assert item is existing


def test_list_items_filters_by_source_type_and_source_id(monkeypatch) -> None:
    from app.repositories import (
        agent_run_repo,
        document_repo,
        knowledge_operation_repo,
        question_log_repo,
    )

    captured = {}

    monkeypatch.setattr(question_log_repo, "list_question_logs", lambda db: [])
    monkeypatch.setattr(question_log_repo, "list_answer_feedback", lambda db: [])
    monkeypatch.setattr(document_repo, "list_documents", lambda db: [])
    monkeypatch.setattr(agent_run_repo, "list_agent_runs", lambda db, **kwargs: [])
    monkeypatch.setattr(agent_run_repo, "list_agent_steps", lambda db, run_id: [])
    monkeypatch.setattr(
        knowledge_operation_repo,
        "list_items",
        lambda db, **kwargs: captured.update(kwargs) or [],
    )
    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_item_by_source",
        lambda db, **kwargs: object(),
    )

    items = knowledge_operations_service.list_items(
        object(),
        knowledge_base_id="kb-1",
        status="pending",
        source_type="agent_run",
        source_id="run-1",
    )

    assert items == []
    assert captured == {
        "knowledge_base_id": "kb-1",
        "status": "pending",
        "source_type": "agent_run",
        "source_id": "run-1",
    }


def test_update_item_reindexed_triggers_document_reindex(monkeypatch) -> None:
    from app.repositories import knowledge_operation_repo
    from app.services import document_service

    captured = {}
    captured_events = []

    def fake_reindex_document(db, doc_id):
        captured["doc_id"] = doc_id
        return SimpleNamespace(doc_id=doc_id)

    def fake_update_item(db, item, *, status=None, resolution_note=None, event=None, draft=None):
        captured["status"] = status
        captured["resolution_note"] = resolution_note
        captured_events.append(event)
        item.status = status
        item.resolution_note = resolution_note
        return item

    monkeypatch.setattr(knowledge_operation_repo, "get_item", lambda db, item_id: _OperationItem())
    monkeypatch.setattr(knowledge_operation_repo, "update_item", fake_update_item)
    monkeypatch.setattr(document_service, "reindex_document", fake_reindex_document)

    item = knowledge_operations_service.update_item(
        object(),
        "item-1",
        status="reindexed",
        resolution_note="Reviewed parse failure.",
        actor_id="manager-1",
    )

    assert item is not None
    assert captured["doc_id"] == "doc-1"
    assert captured["status"] == "reindexed"
    assert captured["resolution_note"] == (
        "Reviewed parse failure.\nReindex queued for document doc-1."
    )
    assert captured_events[0].event_type == "status_updated"
    assert captured_events[0].actor_id == "manager-1"
    assert captured_events[0].detail_json["action_note"] == "Reindex queued for document doc-1."


def test_update_item_document_added_creates_knowledge_draft(monkeypatch) -> None:
    from app.repositories import knowledge_operation_repo

    captured = {}

    class GapItem(_OperationItem):
        source_type = "question_log"
        source_id = "ql-1"
        suggestion_type = "faq_draft"
        title = "Draft missing knowledge answer"
        description = "A question could not be answered."
        suggested_action = "Create an FAQ draft."

    def fake_update_item(db, item, *, status=None, resolution_note=None, event=None, draft=None):
        captured["status"] = status
        captured["resolution_note"] = resolution_note
        captured["event"] = event
        captured["draft"] = draft
        item.status = status
        item.resolution_note = resolution_note
        return item

    monkeypatch.setattr(knowledge_operation_repo, "get_item", lambda db, item_id: GapItem())
    monkeypatch.setattr(knowledge_operation_repo, "get_draft_by_item", lambda db, item_id: None)
    monkeypatch.setattr(knowledge_operation_repo, "update_item", fake_update_item)

    item = knowledge_operations_service.update_item(
        object(),
        "item-1",
        status="document_added",
        resolution_note="Added source note.",
        actor_id="manager-1",
    )

    assert item is not None
    assert captured["status"] == "document_added"
    assert captured["draft"].draft_type == "faq"
    assert captured["draft"].created_by == "manager-1"
    assert captured["event"].detail_json["action_detail"]["draft_id"] == captured["draft"].draft_id
    assert "Knowledge draft created" in captured["resolution_note"]


def test_update_item_reindexed_requires_document_id(monkeypatch) -> None:
    from app.repositories import knowledge_operation_repo

    class OperationWithoutDocument(_OperationItem):
        doc_id = None

    monkeypatch.setattr(
        knowledge_operation_repo,
        "get_item",
        lambda db, item_id: OperationWithoutDocument(),
    )

    try:
        knowledge_operations_service.update_item(
            object(),
            "item-1",
            status="reindexed",
            resolution_note="",
        )
    except ValueError as exc:
        assert "without a document id" in str(exc)
    else:
        raise AssertionError("expected ValueError")
