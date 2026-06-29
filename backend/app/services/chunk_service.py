"""Text chunking service.

Splits parsed pages into overlapping chunks while preserving source
provenance (doc_id, page range, chunk index). Per RULE.md §6.3, every chunk
must carry its origin so answers can trace back to the source.
"""

from __future__ import annotations

from dataclasses import dataclass

import tiktoken

from app.core.config import get_settings
from app.services.parser_service import ParsedDocument


@dataclass
class TextChunk:
    """A chunk of text with source provenance."""

    text: str
    page_start: int
    page_end: int
    chunk_index: int
    token_count: int
    chunk_type: str = "paragraph"
    section: str = ""


def _count_tokens(text: str, encoding: tiktoken.Encoding) -> int:
    return len(encoding.encode(text))


def chunk_document(
    parsed: ParsedDocument,
    doc_id: str,
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[TextChunk]:
    """Split a parsed document into overlapping chunks.

    Pages are concatenated into a single text stream with page-boundary
    markers so that each chunk can be mapped back to its page range. Chunks
    are sized by approximate token count.

    Args:
        parsed: The parsed document from :func:`parse_pdf`.
        doc_id: The document id (stored on each chunk's provenance).
        chunk_size: Target tokens per chunk (defaults to settings).
        chunk_overlap: Overlap tokens between chunks (defaults to settings).

    Returns:
        A list of :class:`TextChunk` with page ranges and indices.
    """
    settings = get_settings()
    target_size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    encoding = tiktoken.get_encoding("cl100k_base")

    # Build a flat stream of (text, page) tokens so we can recover page ranges.
    spans: list[tuple[str, int]] = []
    for p in parsed.pages:
        text = p.text.strip()
        if not text:
            continue
        # Split page text into paragraphs to keep chunk boundaries natural.
        for para in text.split("\n\n"):
            para = para.strip()
            if para:
                spans.append((para, p.page))

    if not spans:
        return []

    chunks: list[TextChunk] = []
    current_parts: list[str] = []
    current_pages: list[int] = []
    current_tokens = 0
    chunk_index = 0

    def flush() -> None:
        nonlocal current_parts, current_pages, current_tokens, chunk_index
        if not current_parts:
            return
        text = "\n\n".join(current_parts)
        pages = sorted(set(current_pages))
        chunks.append(
            TextChunk(
                text=text,
                page_start=pages[0],
                page_end=pages[-1],
                chunk_index=chunk_index,
                token_count=_count_tokens(text, encoding),
                section="",
            )
        )
        chunk_index += 1
        current_parts = []
        current_pages = []
        current_tokens = 0

    for para, page in spans:
        para_tokens = _count_tokens(para, encoding)
        # If a single paragraph exceeds the target size, it still becomes its
        # own chunk rather than being split mid-sentence.
        if current_parts and current_tokens + para_tokens > target_size:
            flush()
            # Carry overlap: keep the last paragraph as the start of the next.
            if overlap > 0 and chunks:
                last_text = chunks[-1].text
                last_parts = last_text.split("\n\n")
                if last_parts:
                    carry = last_parts[-1]
                    current_parts.append(carry)
                    current_pages.append(page)
                    current_tokens = _count_tokens(carry, encoding)
        current_parts.append(para)
        current_pages.append(page)
        current_tokens += para_tokens

    flush()
    return chunks
