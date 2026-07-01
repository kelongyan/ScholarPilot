"""add operation drafts and eval metrics

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-01 10:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: str | Sequence[str] | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_operation_drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("draft_id", sa.String(length=128), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("knowledge_base_id", sa.String(length=128), nullable=True),
        sa.Column("doc_id", sa.String(length=128), nullable=True),
        sa.Column("question_log_id", sa.String(length=128), nullable=True),
        sa.Column("draft_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("source_note", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.doc_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["knowledge_operation_items.item_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"],
            ["knowledge_bases.knowledge_base_id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["question_log_id"],
            ["question_logs.question_log_id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("draft_id"),
    )
    op.create_index(
        "ix_knowledge_operation_drafts_draft_id",
        "knowledge_operation_drafts",
        ["draft_id"],
        unique=True,
    )
    op.create_index(
        "ix_knowledge_operation_drafts_item_id",
        "knowledge_operation_drafts",
        ["item_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_drafts_knowledge_base_id",
        "knowledge_operation_drafts",
        ["knowledge_base_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_drafts_doc_id",
        "knowledge_operation_drafts",
        ["doc_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_drafts_question_log_id",
        "knowledge_operation_drafts",
        ["question_log_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_drafts_draft_type",
        "knowledge_operation_drafts",
        ["draft_type"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_drafts_status",
        "knowledge_operation_drafts",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_drafts_created_by",
        "knowledge_operation_drafts",
        ["created_by"],
        unique=False,
    )

    op.add_column(
        "evaluation_runs",
        sa.Column("metrics_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.add_column(
        "evaluation_run_items",
        sa.Column("metrics_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )


def downgrade() -> None:
    op.drop_column("evaluation_run_items", "metrics_json")
    op.drop_column("evaluation_runs", "metrics_json")

    op.drop_index(
        "ix_knowledge_operation_drafts_created_by",
        table_name="knowledge_operation_drafts",
    )
    op.drop_index("ix_knowledge_operation_drafts_status", table_name="knowledge_operation_drafts")
    op.drop_index(
        "ix_knowledge_operation_drafts_draft_type",
        table_name="knowledge_operation_drafts",
    )
    op.drop_index(
        "ix_knowledge_operation_drafts_question_log_id",
        table_name="knowledge_operation_drafts",
    )
    op.drop_index("ix_knowledge_operation_drafts_doc_id", table_name="knowledge_operation_drafts")
    op.drop_index(
        "ix_knowledge_operation_drafts_knowledge_base_id",
        table_name="knowledge_operation_drafts",
    )
    op.drop_index("ix_knowledge_operation_drafts_item_id", table_name="knowledge_operation_drafts")
    op.drop_index("ix_knowledge_operation_drafts_draft_id", table_name="knowledge_operation_drafts")
    op.drop_table("knowledge_operation_drafts")
