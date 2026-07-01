"""add document lifecycle fields

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-07-01 15:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8d9e0f1a2b3"
down_revision: str | Sequence[str] | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("content_hash", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column(
        "documents",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "documents",
        sa.Column(
            "lifecycle_status",
            sa.String(length=32),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "documents",
        sa.Column("replaces_doc_id", sa.String(length=128), nullable=False, server_default=""),
    )
    op.add_column(
        "documents",
        sa.Column("replaced_by_doc_id", sa.String(length=128), nullable=False, server_default=""),
    )
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"], unique=False)
    op.create_index(
        "ix_documents_lifecycle_status",
        "documents",
        ["lifecycle_status"],
        unique=False,
    )
    op.create_index("ix_documents_replaces_doc_id", "documents", ["replaces_doc_id"], unique=False)
    op.create_index(
        "ix_documents_replaced_by_doc_id",
        "documents",
        ["replaced_by_doc_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_documents_replaced_by_doc_id", table_name="documents")
    op.drop_index("ix_documents_replaces_doc_id", table_name="documents")
    op.drop_index("ix_documents_lifecycle_status", table_name="documents")
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_column("documents", "replaced_by_doc_id")
    op.drop_column("documents", "replaces_doc_id")
    op.drop_column("documents", "lifecycle_status")
    op.drop_column("documents", "version")
    op.drop_column("documents", "content_hash")
