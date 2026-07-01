"""add governance memberships

Revision ID: b7c8d9e0f1a2
Revises: a7b8c9d0e1f2
Create Date: 2026-07-01 13:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: str | Sequence[str] | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=256), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_accounts_user_id", "user_accounts", ["user_id"], unique=True)
    op.create_index("ix_user_accounts_email", "user_accounts", ["email"], unique=False)
    op.create_index("ix_user_accounts_status", "user_accounts", ["status"], unique=False)
    op.create_index("ix_user_accounts_role", "user_accounts", ["role"], unique=False)

    op.create_table(
        "knowledge_base_members",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("membership_id", sa.String(length=128), nullable=False),
        sa.Column("knowledge_base_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"],
            ["knowledge_bases.knowledge_base_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user_accounts.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "knowledge_base_id",
            "user_id",
            name="uq_knowledge_base_members_kb_user",
        ),
        sa.UniqueConstraint("membership_id"),
    )
    op.create_index(
        "ix_knowledge_base_members_membership_id",
        "knowledge_base_members",
        ["membership_id"],
        unique=True,
    )
    op.create_index(
        "ix_knowledge_base_members_knowledge_base_id",
        "knowledge_base_members",
        ["knowledge_base_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_base_members_user_id",
        "knowledge_base_members",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_base_members_role",
        "knowledge_base_members",
        ["role"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_base_members_status",
        "knowledge_base_members",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_base_members_status", table_name="knowledge_base_members")
    op.drop_index("ix_knowledge_base_members_role", table_name="knowledge_base_members")
    op.drop_index("ix_knowledge_base_members_user_id", table_name="knowledge_base_members")
    op.drop_index(
        "ix_knowledge_base_members_knowledge_base_id",
        table_name="knowledge_base_members",
    )
    op.drop_index(
        "ix_knowledge_base_members_membership_id",
        table_name="knowledge_base_members",
    )
    op.drop_table("knowledge_base_members")

    op.drop_index("ix_user_accounts_role", table_name="user_accounts")
    op.drop_index("ix_user_accounts_status", table_name="user_accounts")
    op.drop_index("ix_user_accounts_email", table_name="user_accounts")
    op.drop_index("ix_user_accounts_user_id", table_name="user_accounts")
    op.drop_table("user_accounts")
