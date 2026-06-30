"""add chat traces

Revision ID: c4f2f9d1a7e8
Revises: 8e4d2b76a3c1
Create Date: 2026-06-30 10:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4f2f9d1a7e8"
down_revision: str | Sequence[str] | None = "8e4d2b76a3c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_traces",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("question_log_id", sa.String(length=128), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("rewritten_query", sa.Text(), nullable=False),
        sa.Column("dense_results_json", sa.JSON(), nullable=False),
        sa.Column("sparse_results_json", sa.JSON(), nullable=False),
        sa.Column("fused_results_json", sa.JSON(), nullable=False),
        sa.Column("reranked_results_json", sa.JSON(), nullable=False),
        sa.Column("evidence_pack_json", sa.JSON(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("citations_json", sa.JSON(), nullable=False),
        sa.Column("answer_status", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_log_id"], ["question_logs.question_log_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trace_id"),
        sa.UniqueConstraint("question_log_id"),
    )
    op.create_index("ix_chat_traces_trace_id", "chat_traces", ["trace_id"], unique=True)
    op.create_index(
        "ix_chat_traces_question_log_id",
        "chat_traces",
        ["question_log_id"],
        unique=True,
    )
    op.create_index("ix_chat_traces_answer_status", "chat_traces", ["answer_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chat_traces_answer_status", table_name="chat_traces")
    op.drop_index("ix_chat_traces_question_log_id", table_name="chat_traces")
    op.drop_index("ix_chat_traces_trace_id", table_name="chat_traces")
    op.drop_table("chat_traces")
