"""add knowledge operation events

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-30 18:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "knowledge_operation_items",
        sa.Column("aggregate_key", sa.String(length=256), nullable=False, server_default=""),
    )
    op.add_column(
        "knowledge_operation_items",
        sa.Column("signal_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "knowledge_operation_items",
        sa.Column("last_signal_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_knowledge_operation_items_aggregate_key",
        "knowledge_operation_items",
        ["aggregate_key"],
        unique=False,
    )

    op.create_table(
        "knowledge_operation_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("knowledge_base_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("suggestion_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("detail_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(
        "ix_knowledge_operation_events_event_id",
        "knowledge_operation_events",
        ["event_id"],
        unique=True,
    )
    op.create_index(
        "ix_knowledge_operation_events_item_id",
        "knowledge_operation_events",
        ["item_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_events_knowledge_base_id",
        "knowledge_operation_events",
        ["knowledge_base_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_events_event_type",
        "knowledge_operation_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_events_actor_id",
        "knowledge_operation_events",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_events_source_type",
        "knowledge_operation_events",
        ["source_type"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_events_source_id",
        "knowledge_operation_events",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_events_suggestion_type",
        "knowledge_operation_events",
        ["suggestion_type"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_operation_events_status",
        "knowledge_operation_events",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_operation_events_status", table_name="knowledge_operation_events")
    op.drop_index(
        "ix_knowledge_operation_events_suggestion_type",
        table_name="knowledge_operation_events",
    )
    op.drop_index(
        "ix_knowledge_operation_events_source_id",
        table_name="knowledge_operation_events",
    )
    op.drop_index(
        "ix_knowledge_operation_events_source_type",
        table_name="knowledge_operation_events",
    )
    op.drop_index("ix_knowledge_operation_events_actor_id", table_name="knowledge_operation_events")
    op.drop_index(
        "ix_knowledge_operation_events_event_type",
        table_name="knowledge_operation_events",
    )
    op.drop_index(
        "ix_knowledge_operation_events_knowledge_base_id",
        table_name="knowledge_operation_events",
    )
    op.drop_index("ix_knowledge_operation_events_item_id", table_name="knowledge_operation_events")
    op.drop_index("ix_knowledge_operation_events_event_id", table_name="knowledge_operation_events")
    op.drop_table("knowledge_operation_events")

    op.drop_index(
        "ix_knowledge_operation_items_aggregate_key",
        table_name="knowledge_operation_items",
    )
    op.drop_column("knowledge_operation_items", "last_signal_at")
    op.drop_column("knowledge_operation_items", "signal_count")
    op.drop_column("knowledge_operation_items", "aggregate_key")
