"""Knowledge operations item generation and handling."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import KnowledgeOperationDraft, KnowledgeOperationEvent, KnowledgeOperationItem
from app.repositories import (
    agent_run_repo,
    document_repo,
    knowledge_operation_repo,
    question_log_repo,
)
from app.schemas.knowledge_operations import (
    KnowledgeOperationItemResponse,
    KnowledgeOperationSuggestionResponse,
)


@dataclass(frozen=True)
class OperationDraft:
    """Generated draft before it is persisted as an operation item."""

    knowledge_base_id: str | None
    doc_id: str | None
    question_log_id: str | None
    source_type: str
    source_id: str
    suggestion_type: str
    severity: str
    title: str
    description: str
    suggested_action: str
    aggregate_key: str = ""
    signal_at: datetime | None = None
    agent_run_id: str | None = None


@dataclass(frozen=True)
class HandlingActionResult:
    """Result of an operation handling action."""

    note: str = ""
    detail_json: dict[str, object] = field(default_factory=dict)
    draft: KnowledgeOperationDraft | None = None


def list_items(
    db: Session,
    *,
    knowledge_base_id: str | None = None,
    status: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
) -> list[KnowledgeOperationItem]:
    """Sync generated operation signals into persisted items, then list them."""
    _sync_generated_items(db, knowledge_base_id=knowledge_base_id)
    return knowledge_operation_repo.list_items(
        db,
        knowledge_base_id=knowledge_base_id,
        status=status,
        source_type=source_type,
        source_id=source_id,
    )


def get_item(db: Session, item_id: str) -> KnowledgeOperationItem | None:
    """Get a persisted operation item."""
    return knowledge_operation_repo.get_item(db, item_id)


def list_item_events(db: Session, *, item_id: str) -> list[KnowledgeOperationEvent]:
    """List structured lifecycle events for an operation item."""
    return knowledge_operation_repo.list_events(db, item_id=item_id)


def list_drafts(
    db: Session,
    *,
    knowledge_base_id: str | None = None,
    item_id: str | None = None,
    status: str | None = None,
) -> list[KnowledgeOperationDraft]:
    """List draft knowledge assets created from operation handling."""
    return knowledge_operation_repo.list_drafts(
        db,
        knowledge_base_id=knowledge_base_id,
        item_id=item_id,
        status=status,
    )


def update_item(
    db: Session,
    item_id: str,
    *,
    status: str,
    resolution_note: str = "",
    actor_id: str = "system",
) -> KnowledgeOperationItem | None:
    """Update handling status for a persisted operation item.

    Some statuses are actionable: they execute a repair step before the item is
    marked handled. This keeps the operations list tied to real remediation
    work instead of being only a manual checklist.
    """
    item = knowledge_operation_repo.get_item(db, item_id)
    if item is None:
        return None
    action_result = _apply_handling_action(db, item, status, actor_id=actor_id)
    merged_note = _merge_resolution_notes(resolution_note, action_result.note)
    event = _handling_event(
        item,
        status=status,
        actor_id=actor_id,
        resolution_note=resolution_note,
        action_note=action_result.note,
        action_detail=action_result.detail_json,
    )
    return knowledge_operation_repo.update_item(
        db,
        item,
        status=status,
        resolution_note=merged_note,
        event=event,
        draft=action_result.draft,
    )


def list_suggestions(
    db: Session,
    *,
    knowledge_base_id: str | None = None,
) -> list[KnowledgeOperationSuggestionResponse]:
    """Backward-compatible suggestion list backed by persisted items."""
    items = list_items(db, knowledge_base_id=knowledge_base_id, status="pending")
    return [_suggestion_from_item(item) for item in items]


def list_run_suggestions(
    db: Session,
    *,
    run_id: str,
) -> list[KnowledgeOperationSuggestionResponse]:
    """Generate or retrieve operation items tied to a specific Agent run."""
    item = sync_agent_run_item(db, run_id=run_id)
    if item is None:
        return []
    return [_suggestion_from_item(item)]


def sync_agent_run_item(db: Session, *, run_id: str) -> KnowledgeOperationItem | None:
    """Persist or reuse an Agent run review item."""
    try:
        run = agent_run_repo.get_agent_run(db, run_id)
        if run is None:
            return None
        steps = agent_run_repo.list_agent_steps(db, run_id)
        draft = _agent_run_draft(run, steps)
        if draft is None:
            return None
        return _sync_draft(db, draft)
    except Exception:  # noqa: BLE001
        _rollback_if_possible(db)
        return None


def _sync_generated_items(
    db: Session,
    *,
    knowledge_base_id: str | None,
) -> None:
    for draft in _generate_drafts(db, knowledge_base_id=knowledge_base_id):
        _sync_draft(db, draft)


def _generate_drafts(
    db: Session,
    *,
    knowledge_base_id: str | None,
) -> list[OperationDraft]:
    drafts: list[OperationDraft] = []
    question_logs = [
        log
        for log in question_log_repo.list_question_logs(db)
        if _matches_knowledge_base(log.knowledge_base_id, knowledge_base_id)
    ]
    feedback_by_question_log_id = {
        feedback.question_log_id: feedback
        for feedback in question_log_repo.list_answer_feedback(db)
    }

    for log in question_logs:
        if log.answer_status != "answered":
            drafts.append(_no_answer_draft(log))
            continue

        feedback = feedback_by_question_log_id.get(log.question_log_id)
        if feedback and feedback.useful is False:
            drafts.append(_poor_answer_draft(log, feedback))
        elif feedback and feedback.citation_accurate is False:
            drafts.append(_citation_review_draft(log, feedback))

    for doc in document_repo.list_documents(db):
        if not _matches_knowledge_base(doc.knowledge_base_id, knowledge_base_id):
            continue
        if getattr(doc, "lifecycle_status", "active") != "active":
            continue
        if doc.status == "failed":
            drafts.append(_failed_document_draft(doc))

    for draft in _generate_agent_run_drafts(db, knowledge_base_id=knowledge_base_id):
        drafts.append(draft)

    return drafts


def _generate_agent_run_drafts(
    db: Session,
    *,
    knowledge_base_id: str | None,
) -> list[OperationDraft]:
    try:
        runs = agent_run_repo.list_agent_runs(db, knowledge_base_id=knowledge_base_id)
    except Exception:  # noqa: BLE001
        _rollback_if_possible(db)
        return []

    drafts: list[OperationDraft] = []
    for run in runs:
        try:
            steps = agent_run_repo.list_agent_steps(db, run.run_id)
            draft = _agent_run_draft(run, steps)
        except Exception:  # noqa: BLE001
            _rollback_if_possible(db)
            continue
        if draft is not None:
            drafts.append(draft)
    return drafts


def _matches_knowledge_base(
    item_knowledge_base_id: str | None,
    requested_knowledge_base_id: str | None,
) -> bool:
    if requested_knowledge_base_id is None:
        return True
    return item_knowledge_base_id == requested_knowledge_base_id


def _no_answer_draft(log) -> OperationDraft:
    return OperationDraft(
        knowledge_base_id=log.knowledge_base_id,
        doc_id=log.doc_id,
        question_log_id=log.question_log_id,
        source_type="question_log",
        source_id=log.question_log_id,
        suggestion_type="faq_draft",
        aggregate_key=_knowledge_gap_aggregate_key(log),
        signal_at=getattr(log, "created_at", None),
        severity="high",
        title="Draft missing knowledge answer",
        description=(
            "A question could not be answered from the indexed evidence. "
            "This is a candidate knowledge gap."
        ),
        suggested_action=(
            "Create an FAQ draft or upload source material that answers this question."
        ),
    )


def _poor_answer_draft(log, feedback) -> OperationDraft:
    return OperationDraft(
        knowledge_base_id=log.knowledge_base_id,
        doc_id=log.doc_id,
        question_log_id=log.question_log_id,
        source_type="answer_feedback",
        source_id=feedback.feedback_id,
        suggestion_type="answer_quality_review",
        aggregate_key=_feedback_aggregate_key(log, "answer_quality_review"),
        signal_at=getattr(feedback, "created_at", None),
        severity="medium",
        title="Review answer marked not useful",
        description="A user marked this answer as not useful.",
        suggested_action=(
            "Review the answer, citations, and source coverage before updating the "
            "knowledge base."
        ),
    )


def _citation_review_draft(log, feedback) -> OperationDraft:
    return OperationDraft(
        knowledge_base_id=log.knowledge_base_id,
        doc_id=log.doc_id,
        question_log_id=log.question_log_id,
        source_type="answer_feedback",
        source_id=feedback.feedback_id,
        suggestion_type="citation_review",
        aggregate_key=_feedback_aggregate_key(log, "citation_review"),
        signal_at=getattr(feedback, "created_at", None),
        severity="medium",
        title="Review inaccurate citation feedback",
        description="A user reported that the answer citation was inaccurate.",
        suggested_action=(
            "Inspect the cited chunks and improve source documents or retrieval settings."
        ),
    )


def _failed_document_draft(doc) -> OperationDraft:
    return OperationDraft(
        knowledge_base_id=doc.knowledge_base_id,
        doc_id=doc.doc_id,
        question_log_id=None,
        source_type="document",
        source_id=doc.doc_id,
        suggestion_type="reindex_document",
        aggregate_key=_source_aggregate_key(
            knowledge_base_id=doc.knowledge_base_id,
            source_type="document",
            source_id=doc.doc_id,
            suggestion_type="reindex_document",
        ),
        signal_at=getattr(doc, "updated_at", None),
        severity="high",
        title="Fix failed document processing",
        description="A source document failed parsing, embedding, or indexing.",
        suggested_action=(
            "Inspect the error, replace the source file if needed, then reindex the document."
        ),
    )


def _sync_draft(db: Session, draft: OperationDraft) -> KnowledgeOperationItem | None:
    existing_signal = knowledge_operation_repo.get_event_by_source(
        db,
        event_type="signal_detected",
        source_type=draft.source_type,
        source_id=draft.source_id,
        suggestion_type=draft.suggestion_type,
    )
    if existing_signal is not None:
        return knowledge_operation_repo.get_item(db, existing_signal.item_id)

    existing = knowledge_operation_repo.get_item_by_source(
        db,
        source_type=draft.source_type,
        source_id=draft.source_id,
        suggestion_type=draft.suggestion_type,
    )
    if existing is not None:
        _record_signal_event(db, existing, draft)
        return existing

    aggregate_key = draft.aggregate_key or _source_aggregate_key(
        knowledge_base_id=draft.knowledge_base_id,
        source_type=draft.source_type,
        source_id=draft.source_id,
        suggestion_type=draft.suggestion_type,
    )
    aggregate = knowledge_operation_repo.get_pending_item_by_aggregate_key(
        db,
        aggregate_key=aggregate_key,
    )
    if aggregate is not None:
        _record_signal_event(db, aggregate, draft, increment_count=True)
        return aggregate

    item = _create_item_from_draft(db, draft)
    if item is not None:
        _record_signal_event(db, item, draft)
    return item


def _create_item_from_draft(
    db: Session,
    draft: OperationDraft,
) -> KnowledgeOperationItem | None:
    aggregate_key = draft.aggregate_key or _source_aggregate_key(
        knowledge_base_id=draft.knowledge_base_id,
        source_type=draft.source_type,
        source_id=draft.source_id,
        suggestion_type=draft.suggestion_type,
    )
    try:
        return knowledge_operation_repo.create_item(
            db,
            KnowledgeOperationItem(
                item_id=str(uuid.uuid4()),
                knowledge_base_id=draft.knowledge_base_id,
                doc_id=draft.doc_id,
                question_log_id=draft.question_log_id,
                agent_run_id=draft.agent_run_id,
                source_type=draft.source_type,
                source_id=draft.source_id,
                suggestion_type=draft.suggestion_type,
                aggregate_key=aggregate_key,
                signal_count=1,
                last_signal_at=draft.signal_at,
                severity=draft.severity,
                title=draft.title,
                description=draft.description,
                suggested_action=draft.suggested_action,
                status="pending",
            ),
        )
    except Exception:  # noqa: BLE001
        _rollback_if_possible(db)
        return None


def _record_signal_event(
    db: Session,
    item: KnowledgeOperationItem,
    draft: OperationDraft,
    *,
    increment_count: bool = False,
) -> None:
    try:
        event = KnowledgeOperationEvent(
            event_id=str(uuid.uuid4()),
            item_id=item.item_id,
            knowledge_base_id=item.knowledge_base_id,
            event_type="signal_detected",
            actor_id="system",
            source_type=draft.source_type,
            source_id=draft.source_id,
            suggestion_type=draft.suggestion_type,
            status=item.status,
            note=draft.description,
            detail_json={
                "title": draft.title,
                "severity": draft.severity,
                "suggested_action": draft.suggested_action,
                "doc_id": draft.doc_id,
                "question_log_id": draft.question_log_id,
                "agent_run_id": draft.agent_run_id,
            },
        )
        knowledge_operation_repo.create_event(db, event, commit=False)
        if increment_count:
            item.signal_count = int(getattr(item, "signal_count", 1) or 1) + 1
        if draft.signal_at is not None:
            item.last_signal_at = draft.signal_at
        db.commit()
    except Exception:  # noqa: BLE001
        _rollback_if_possible(db)


def _apply_handling_action(
    db: Session,
    item: KnowledgeOperationItem,
    status: str,
    *,
    actor_id: str,
) -> HandlingActionResult:
    """Run the repair action implied by a handling status, when one exists."""
    if status == "document_added":
        return _create_source_material_draft(db, item, actor_id)
    if status != "reindexed":
        return HandlingActionResult()
    if not item.doc_id:
        raise ValueError("Cannot reindex an operation item without a document id.")

    from app.services import document_service

    document = document_service.reindex_document(db, item.doc_id)
    if document is None:
        raise ValueError(f"Document not found for reindex: {item.doc_id}")
    return HandlingActionResult(
        note=f"Reindex queued for document {item.doc_id}.",
        detail_json={"doc_id": item.doc_id, "action": "reindex_queued"},
    )


def _create_source_material_draft(
    db: Session,
    item: KnowledgeOperationItem,
    actor_id: str,
) -> HandlingActionResult:
    """Create or reuse a draft knowledge asset for a gap/quality operation."""
    existing = knowledge_operation_repo.get_draft_by_item(db, item_id=item.item_id)
    if existing is not None:
        return HandlingActionResult(
            note=f"Knowledge draft already exists: {existing.draft_id}.",
            detail_json={"draft_id": existing.draft_id, "action": "draft_reused"},
        )

    draft = KnowledgeOperationDraft(
        draft_id=str(uuid.uuid4()),
        item_id=item.item_id,
        knowledge_base_id=item.knowledge_base_id,
        doc_id=item.doc_id,
        question_log_id=item.question_log_id,
        draft_type=_draft_type_for_item(item),
        status="draft",
        title=_draft_title(item),
        question=_draft_question(item),
        answer="",
        source_note=_draft_source_note(item),
        created_by=actor_id,
    )
    return HandlingActionResult(
        note=f"Knowledge draft created: {draft.draft_id}.",
        detail_json={
            "draft_id": draft.draft_id,
            "draft_type": draft.draft_type,
            "action": "draft_created",
        },
        draft=draft,
    )


def _merge_resolution_notes(user_note: str, action_note: str) -> str:
    notes = [note.strip() for note in (user_note, action_note) if note.strip()]
    return "\n".join(notes)


def _handling_event(
    item: KnowledgeOperationItem,
    *,
    status: str,
    actor_id: str,
    resolution_note: str,
    action_note: str,
    action_detail: dict[str, object],
) -> KnowledgeOperationEvent:
    return KnowledgeOperationEvent(
        event_id=str(uuid.uuid4()),
        item_id=item.item_id,
        knowledge_base_id=item.knowledge_base_id,
        event_type="status_updated",
        actor_id=actor_id,
        source_type=item.source_type,
        source_id=item.source_id,
        suggestion_type=item.suggestion_type,
        status=status,
        note=_merge_resolution_notes(resolution_note, action_note),
        detail_json={
            "previous_status": item.status,
            "status": status,
            "resolution_note": resolution_note,
            "action_note": action_note,
            "action_detail": action_detail,
            "doc_id": item.doc_id,
            "question_log_id": item.question_log_id,
            "agent_run_id": item.agent_run_id,
        },
    )


def _draft_type_for_item(item: KnowledgeOperationItem) -> str:
    if item.suggestion_type == "faq_draft":
        return "faq"
    if item.suggestion_type == "citation_review":
        return "citation_fix"
    if item.suggestion_type == "answer_quality_review":
        return "answer_improvement"
    return "source_material"


def _draft_title(item: KnowledgeOperationItem) -> str:
    if item.suggestion_type == "faq_draft":
        return "Draft FAQ for missing answer"
    if item.suggestion_type == "citation_review":
        return "Draft citation correction"
    if item.suggestion_type == "answer_quality_review":
        return "Draft answer improvement"
    return f"Draft supporting material for {item.title}"


def _draft_question(item: KnowledgeOperationItem) -> str:
    if item.source_type == "question_log" and item.source_id:
        return f"Question log {item.source_id}"
    if item.question_log_id:
        return f"Question log {item.question_log_id}"
    return item.title


def _draft_source_note(item: KnowledgeOperationItem) -> str:
    parts = [
        item.description,
        item.suggested_action,
        f"source_type={item.source_type}",
        f"source_id={item.source_id}",
        f"suggestion_type={item.suggestion_type}",
    ]
    if item.doc_id:
        parts.append(f"doc_id={item.doc_id}")
    if item.question_log_id:
        parts.append(f"question_log_id={item.question_log_id}")
    if item.agent_run_id:
        parts.append(f"agent_run_id={item.agent_run_id}")
    return "\n".join(part for part in parts if part)


def _source_aggregate_key(
    *,
    knowledge_base_id: str | None,
    source_type: str,
    source_id: str,
    suggestion_type: str,
) -> str:
    return "|".join(
        [
            knowledge_base_id or "",
            suggestion_type,
            source_type,
            source_id,
        ]
    )


def _knowledge_gap_aggregate_key(log) -> str:
    scope = log.knowledge_base_id or log.doc_id or ""
    normalized_question = " ".join(str(log.question).lower().split())[:120]
    return f"{scope}|faq_draft|question|{normalized_question}"


def _feedback_aggregate_key(log, suggestion_type: str) -> str:
    scope = log.knowledge_base_id or log.doc_id or ""
    normalized_question = " ".join(str(log.question).lower().split())[:120]
    return f"{scope}|{suggestion_type}|feedback|{normalized_question}"


def _agent_run_draft(run, steps) -> OperationDraft | None:
    review_step = next((step for step in steps if step.agent_name == "reviewer_agent"), None)
    review_status = ""
    unsupported_citation_count = 0
    if review_step is not None:
        review_status = str(review_step.output_json.get("review_status", ""))
        unsupported_citation_count = int(
            review_step.output_json.get("unsupported_citation_count", 0)
        )

    if run.status == "completed" and run.answer_status == "answered" and review_status != "warning":
        return None

    if run.status == "failed":
        severity = "high"
        title = "Review failed Agent run"
    elif run.status == "max_steps_exceeded" or run.answer_status == "max_steps_exceeded":
        severity = "medium"
        title = "Review truncated Agent run"
    elif review_status == "warning" or unsupported_citation_count > 0:
        severity = "medium"
        title = "Review Agent citation warning"
    else:
        severity = "medium"
        title = "Review Agent run outcome"

    description = (
        f"Agent run ended with status '{run.status}' and answer status "
        f"'{run.answer_status}'."
    )
    if review_status == "warning":
        description = (
            f"Agent reviewer flagged {unsupported_citation_count} unsupported citation(s). "
            + description
        )

    return OperationDraft(
        knowledge_base_id=run.knowledge_base_id,
        doc_id=run.doc_id,
        question_log_id=run.question_log_id,
        agent_run_id=run.run_id,
        source_type="agent_run",
        source_id=run.run_id,
        suggestion_type="agent_review",
        signal_at=getattr(run, "created_at", None),
        severity=severity,
        title=title,
        description=description,
        suggested_action=(
            "Inspect the Agent trace, revise retrieval scope or prompt steps, and "
            "convert the run into a reusable operational improvement."
        ),
    )


def _suggestion_from_item(item: KnowledgeOperationItem) -> KnowledgeOperationSuggestionResponse:
    response = KnowledgeOperationItemResponse.model_validate(item)
    return KnowledgeOperationSuggestionResponse(
        suggestion_id=item.item_id,
        item_id=response.item_id,
        knowledge_base_id=response.knowledge_base_id,
        doc_id=response.doc_id,
        question_log_id=response.question_log_id,
        agent_run_id=getattr(response, "agent_run_id", None),
        source_type=response.source_type,
        source_id=response.source_id,
        suggestion_type=response.suggestion_type,
        aggregate_key=response.aggregate_key,
        signal_count=response.signal_count,
        last_signal_at=response.last_signal_at,
        severity=response.severity,
        title=response.title,
        description=response.description,
        suggested_action=response.suggested_action,
        status=response.status,
        resolution_note=response.resolution_note,
        evidence=[
            {
                "source_type": response.source_type,
                "source_id": response.source_id,
            }
        ],
        created_at=response.created_at,
    )


def _rollback_if_possible(db: Session) -> None:
    rollback = getattr(db, "rollback", None)
    if callable(rollback):
        rollback()
