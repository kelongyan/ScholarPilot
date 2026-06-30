"""Agent run repository."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentRun, AgentStep


def create_agent_run(
    db: Session, agent_run: AgentRun, steps: list[AgentStep]
) -> AgentRun:
    db.add(agent_run)
    for step in steps:
        db.add(step)
    db.commit()
    db.refresh(agent_run)
    return agent_run


def get_agent_run(db: Session, run_id: str) -> AgentRun | None:
    return db.scalar(select(AgentRun).where(AgentRun.run_id == run_id))


def list_agent_runs(
    db: Session,
    *,
    knowledge_base_id: str | None = None,
    route: str | None = None,
    status: str | None = None,
    answer_status: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> list[AgentRun]:
    query = select(AgentRun)
    if knowledge_base_id:
        query = query.where(AgentRun.knowledge_base_id == knowledge_base_id)
    if route:
        query = query.where(AgentRun.route == route)
    if status:
        query = query.where(AgentRun.status == status)
    if answer_status:
        query = query.where(AgentRun.answer_status == answer_status)
    if created_from:
        query = query.where(AgentRun.created_at >= created_from)
    if created_to:
        query = query.where(AgentRun.created_at <= created_to)
    return list(db.scalars(query.order_by(AgentRun.created_at.desc())))


def list_agent_steps(db: Session, run_id: str) -> list[AgentStep]:
    return list(
        db.scalars(
            select(AgentStep)
            .where(AgentStep.run_id == run_id)
            .order_by(AgentStep.sequence.asc())
        )
    )
