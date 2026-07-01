"""Async document processing tasks (RQ).

Pipeline: parse source document -> chunk -> embed -> index (Qdrant + Postgres).
Each step updates the document status so the frontend can poll progress.
"""

from __future__ import annotations

import logging
import uuid

from app.core.db import SessionLocal
from app.models import Chunk
from app.repositories import document_repo
from app.services.chunk_service import chunk_document
from app.services.embedding_service import embed_texts
from app.services.parser_service import parse_document
from app.services.vector_service import delete_document_vectors, index_chunks

logger = logging.getLogger(__name__)


def process_document(doc_id: str) -> None:
    """Parse, chunk, embed, and index a document.

    Args:
        doc_id: The document id to process.
    """
    db = SessionLocal()
    try:
        doc = document_repo.get_document(db, doc_id)
        if doc is None:
            logger.error("Document not found: %s", doc_id)
            return
        knowledge_base_id = doc.knowledge_base_id

        # --- Parse ---
        document_repo.update_status(db, doc_id, "parsing")
        try:
            parsed = parse_document(doc.file_path, source=doc.source)
        except Exception as e:  # noqa: BLE001
            document_repo.update_status(
                db, doc_id, "failed", error_message=f"parse error: {e}"
            )
            logger.exception("Parse failed for %s", doc_id)
            return

        document_repo.update_status(
            db, doc_id, "parsed", page_count=parsed.page_count
        )

        # --- Chunk ---
        text_chunks = chunk_document(parsed, doc_id)
        if not text_chunks:
            document_repo.update_status(
                db, doc_id, "failed", error_message="no text extracted from document"
            )
            return

        # --- Embed ---
        document_repo.update_status(db, doc_id, "indexing")
        try:
            vectors = embed_texts([c.text for c in text_chunks])
        except Exception as e:  # noqa: BLE001
            document_repo.update_status(
                db, doc_id, "failed", error_message=f"embedding error: {e}"
            )
            logger.exception("Embedding failed for %s", doc_id)
            return

        # --- Index ---
        # Remove any previous vectors/chunks (reindex path).
        delete_document_vectors(doc_id)
        document_repo.delete_document_chunks(db, doc_id)

        chunk_dicts = [
            {
                "chunk_id": str(uuid.uuid4()),
                "text": c.text,
                "section": c.section,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "chunk_type": c.chunk_type,
                "chunk_index": c.chunk_index,
            }
            for c in text_chunks
        ]
        index_chunks(
            doc_id,
            chunk_dicts,
            vectors,
            knowledge_base_id=knowledge_base_id,
        )

        chunk_models = [
            Chunk(
                chunk_id=cd["chunk_id"],
                doc_id=doc_id,
                section=cd["section"],
                page_start=cd["page_start"],
                page_end=cd["page_end"],
                text=cd["text"],
                chunk_type=cd["chunk_type"],
                token_count=text_chunks[i].token_count,
                chunk_index=cd["chunk_index"],
            )
            for i, cd in enumerate(chunk_dicts)
        ]
        document_repo.create_chunks(db, chunk_models)

        document_repo.update_status(db, doc_id, "indexed")
        logger.info("Indexed document %s (%d chunks)", doc_id, len(chunk_models))
    finally:
        db.close()
