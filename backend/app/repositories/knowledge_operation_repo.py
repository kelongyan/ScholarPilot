"""Knowledge operation item repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeOperationDraft, KnowledgeOperationEvent, KnowledgeOperationItem


def create_item(db: Session, item: KnowledgeOperationItem) -> KnowledgeOperationItem:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item(db: Session, item_id: str) -> KnowledgeOperationItem | None:
    return db.scalar(
        select(KnowledgeOperationItem).where(
            KnowledgeOperationItem.item_id == item_id
        )
    )


def get_item_by_source(
    db: Session,
    *,
    source_type: str,
    source_id: str,
    suggestion_type: str,
) -> KnowledgeOperationItem | None:
    return db.scalar(
        select(KnowledgeOperationItem).where(
            KnowledgeOperationItem.source_type == source_type,
            KnowledgeOperationItem.source_id == source_id,
            KnowledgeOperationItem.suggestion_type == suggestion_type,
        )
    )


def get_pending_item_by_aggregate_key(
    db: Session,
    *,
    aggregate_key: str,
) -> KnowledgeOperationItem | None:
    if not aggregate_key:
        return None
    return db.scalar(
        select(KnowledgeOperationItem).where(
            KnowledgeOperationItem.aggregate_key == aggregate_key,
            KnowledgeOperationItem.status == "pending",
        )
    )


def list_items(
    db: Session,
    *,
    knowledge_base_id: str | None = None,
    status: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
) -> list[KnowledgeOperationItem]:
    query = select(KnowledgeOperationItem)
    if knowledge_base_id:
        query = query.where(KnowledgeOperationItem.knowledge_base_id == knowledge_base_id)
    if status:
        query = query.where(KnowledgeOperationItem.status == status)
    if source_type:
        query = query.where(KnowledgeOperationItem.source_type == source_type)
    if source_id:
        query = query.where(KnowledgeOperationItem.source_id == source_id)
    return list(
        db.scalars(
            query.order_by(
                KnowledgeOperationItem.status.asc(),
                KnowledgeOperationItem.severity.desc(),
                KnowledgeOperationItem.created_at.desc(),
            )
        )
    )


def update_item(
    db: Session,
    item: KnowledgeOperationItem,
    *,
    status: str | None = None,
    resolution_note: str | None = None,
    event: KnowledgeOperationEvent | None = None,
    draft: KnowledgeOperationDraft | None = None,
) -> KnowledgeOperationItem:
    if status is not None:
        item.status = status
    if resolution_note is not None:
        item.resolution_note = resolution_note
    if event is not None:
        db.add(event)
    if draft is not None:
        db.add(draft)
    db.commit()
    db.refresh(item)
    return item


def get_draft_by_item(
    db: Session,
    *,
    item_id: str,
) -> KnowledgeOperationDraft | None:
    return db.scalar(
        select(KnowledgeOperationDraft).where(KnowledgeOperationDraft.item_id == item_id)
    )


def list_drafts(
    db: Session,
    *,
    knowledge_base_id: str | None = None,
    item_id: str | None = None,
    status: str | None = None,
) -> list[KnowledgeOperationDraft]:
    query = select(KnowledgeOperationDraft)
    if knowledge_base_id:
        query = query.where(KnowledgeOperationDraft.knowledge_base_id == knowledge_base_id)
    if item_id:
        query = query.where(KnowledgeOperationDraft.item_id == item_id)
    if status:
        query = query.where(KnowledgeOperationDraft.status == status)
    return list(db.scalars(query.order_by(KnowledgeOperationDraft.created_at.desc())))


def create_event(
    db: Session,
    event: KnowledgeOperationEvent,
    *,
    commit: bool = True,
) -> KnowledgeOperationEvent:
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    return event


def get_event_by_source(
    db: Session,
    *,
    event_type: str,
    source_type: str,
    source_id: str,
    suggestion_type: str,
) -> KnowledgeOperationEvent | None:
    return db.scalar(
        select(KnowledgeOperationEvent).where(
            KnowledgeOperationEvent.event_type == event_type,
            KnowledgeOperationEvent.source_type == source_type,
            KnowledgeOperationEvent.source_id == source_id,
            KnowledgeOperationEvent.suggestion_type == suggestion_type,
        )
    )


def list_events(
    db: Session,
    *,
    item_id: str,
) -> list[KnowledgeOperationEvent]:
    return list(
        db.scalars(
            select(KnowledgeOperationEvent)
            .where(KnowledgeOperationEvent.item_id == item_id)
            .order_by(KnowledgeOperationEvent.created_at.desc())
        )
    )
