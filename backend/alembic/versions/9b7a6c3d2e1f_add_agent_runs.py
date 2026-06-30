"""add agent runs

Revision ID: 9b7a6c3d2e1f
Revises: c4f2f9d1a7e8
Create Date: 2026-06-30 12:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9b7a6c3d2e1f"
down_revision: str | Sequence[str] | None = "c4f2f9d1a7e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("question_log_id", sa.String(length=128), nullable=True),
        sa.Column("chat_trace_id", sa.String(length=128), nullable=True),
        sa.Column("doc_id", sa.String(length=128), nullable=True),
        sa.Column("knowledge_base_id", sa.String(length=128), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("route", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("answer_status", sa.String(length=32), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("citations_json", sa.JSON(), nullable=False),
        sa.Column("trace_json", sa.JSON(), nullable=False),
        sa.Column("total_latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["chat_trace_id"], ["chat_traces.trace_id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.doc_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"],
            ["knowledge_bases.knowledge_base_id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["question_log_id"], ["question_logs.question_log_id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index("ix_agent_runs_run_id", "agent_runs", ["run_id"], unique=True)
    op.create_index(
        "ix_agent_runs_question_log_id", "agent_runs", ["question_log_id"], unique=False
    )
    op.create_index(
        "ix_agent_runs_chat_trace_id", "agent_runs", ["chat_trace_id"], unique=False
    )
    op.create_index("ix_agent_runs_doc_id", "agent_runs", ["doc_id"], unique=False)
    op.create_index(
        "ix_agent_runs_knowledge_base_id",
        "agent_runs",
        ["knowledge_base_id"],
        unique=False,
    )
    op.create_index("ix_agent_runs_route", "agent_runs", ["route"], unique=False)
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"], unique=False)
    op.create_index(
        "ix_agent_runs_answer_status", "agent_runs", ["answer_status"], unique=False
    )

    op.create_table(
        "agent_steps",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("step_id", sa.String(length=128), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("input_json", sa.JSON(), nullable=False),
        sa.Column("output_json", sa.JSON(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.run_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("step_id"),
    )
    op.create_index("ix_agent_steps_step_id", "agent_steps", ["step_id"], unique=True)
    op.create_index("ix_agent_steps_run_id", "agent_steps", ["run_id"], unique=False)
    op.create_index("ix_agent_steps_status", "agent_steps", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_steps_status", table_name="agent_steps")
    op.drop_index("ix_agent_steps_run_id", table_name="agent_steps")
    op.drop_index("ix_agent_steps_step_id", table_name="agent_steps")
    op.drop_table("agent_steps")
    op.drop_index("ix_agent_runs_answer_status", table_name="agent_runs")
    op.drop_index("ix_agent_runs_status", table_name="agent_runs")
    op.drop_index("ix_agent_runs_route", table_name="agent_runs")
    op.drop_index("ix_agent_runs_knowledge_base_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_doc_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_chat_trace_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_question_log_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_run_id", table_name="agent_runs")
    op.drop_table("agent_runs")
