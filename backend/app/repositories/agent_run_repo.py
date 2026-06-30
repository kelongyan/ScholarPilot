"""Agent run repository."""

from __future__ import annotations

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


def list_agent_runs(db: Session) -> list[AgentRun]:
    return list(db.scalars(select(AgentRun).order_by(AgentRun.created_at.desc())))


def list_agent_steps(db: Session, run_id: str) -> list[AgentStep]:
    return list(
        db.scalars(
            select(AgentStep)
            .where(AgentStep.run_id == run_id)
            .order_by(AgentStep.sequence.asc())
        )
    )
