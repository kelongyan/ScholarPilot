"""Chat service: evidence-first RAG orchestration.

Per RULE.md §6.2, the LLM may only answer from retrieved evidence. When
evidence is insufficient, the system must say so explicitly rather than
fabricate conclusions, metrics, or citations.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.providers import get_llm_provider
from app.services.embedding_service import embed_query
from app.services.vector_service import RetrievedChunk, retrieve

SYSTEM_PROMPT = """You are ScholarPilot, a research assistant that answers \
questions about academic papers using ONLY the provided evidence.

Rules:
- Answer using only the evidence passages below. Do not invent facts, numbers, \
or conclusions not present in the evidence.
- If the evidence is insufficient to answer, say: \
"当前资料不足以支持可靠回答。" and briefly explain what is missing.
- Keep the answer concise and grounded. Quote key phrases when useful.
- Do not fabricate citations. Only reference the evidence provided.
"""


@dataclass
class ChatResult:
    """The result of a chat request: answer plus supporting citations."""

    answer: str
    citations: list[RetrievedChunk]


def answer_question(doc_id: str, question: str) -> ChatResult:
    """Answer a question about a single document using evidence-first RAG.

    Pipeline (Phase 1, dense-only; hybrid + rerank arrive in Phase 2):
        embed(query) -> retrieve(doc_id) -> build context -> LLM answer

    Args:
        doc_id: The document to query against.
        question: The user's question.

    Returns:
        A :class:`ChatResult` with the answer and supporting chunks.
    """
    query_vector = embed_query(question)
    retrieved = retrieve(query_vector, doc_id=doc_id)

    if not retrieved:
        return ChatResult(
            answer="当前资料不足以支持可靠回答。该文档尚未完成索引，或检索未返回相关证据。",
            citations=[],
        )

    context = _build_context(retrieved)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{context}"},
    ]
    llm = get_llm_provider()
    answer = llm.chat(messages, temperature=0.2, max_tokens=1024)

    return ChatResult(answer=answer, citations=retrieved)


def _build_context(retrieved: list[RetrievedChunk]) -> str:
    """Format retrieved chunks into an evidence block for the LLM."""
    parts: list[str] = []
    for i, chunk in enumerate(retrieved, start=1):
        parts.append(
            f"[{i}] (page {chunk.page_start}) {chunk.text}"
        )
    return "\n\n".join(parts)
