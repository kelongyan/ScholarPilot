"""initial schema documents chunks citations

Revision ID: 7a6442d093d5
Revises:
Create Date: 2026-06-29 08:15:27.974095

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a6442d093d5"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create documents, chunks, and citations tables."""
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("doc_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doc_id"),
    )
    op.create_index("ix_documents_doc_id", "documents", ["doc_id"], unique=True)
    op.create_index("ix_documents_status", "documents", ["status"], unique=False)

    op.create_table(
        "chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("chunk_id", sa.String(length=128), nullable=False),
        sa.Column("doc_id", sa.String(length=128), nullable=False),
        sa.Column("section", sa.String(length=256), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("chunk_type", sa.String(length=32), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["doc_id"], ["documents.doc_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index("ix_chunks_chunk_id", "chunks", ["chunk_id"], unique=True)
    op.create_index("ix_chunks_doc_id", "chunks", ["doc_id"], unique=False)

    op.create_table(
        "citations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("citation_id", sa.String(length=128), nullable=False),
        sa.Column("chunk_id", sa.String(length=128), nullable=False),
        sa.Column("doc_id", sa.String(length=128), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.chunk_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("citation_id"),
    )
    op.create_index("ix_citations_citation_id", "citations", ["citation_id"], unique=True)
    op.create_index("ix_citations_chunk_id", "citations", ["chunk_id"], unique=False)
    op.create_index("ix_citations_doc_id", "citations", ["doc_id"], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("ix_citations_doc_id", table_name="citations")
    op.drop_index("ix_citations_chunk_id", table_name="citations")
    op.drop_index("ix_citations_citation_id", table_name="citations")
    op.drop_table("citations")
    op.drop_index("ix_chunks_doc_id", table_name="chunks")
    op.drop_index("ix_chunks_chunk_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_doc_id", table_name="documents")
    op.drop_table("documents")
