"""Chat service: evidence-first RAG orchestration.

Per RULE.md section 6.2, the LLM may only answer from retrieved evidence. When
evidence is insufficient, the system must say so explicitly rather than
fabricate conclusions, metrics, or citations.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.providers import get_llm_provider
from app.schemas.rag import RetrievalTraceResponse
from app.services.retrieval_service import RetrievalResult, run_hybrid_retrieval

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "Insufficient evidence in the current knowledge base to provide a reliable answer."
)

SYSTEM_PROMPT = "\n".join(
    [
        (
            "You are Kairos, a verifiable team knowledge-base assistant that answers "
            "questions using ONLY the provided evidence."
        ),
        "",
        "Rules:",
        (
            "- Answer using only the evidence passages below. Do not invent facts, "
            "numbers, or conclusions not present in the evidence."
        ),
        (
            f'- If the evidence is insufficient to answer, say: "{INSUFFICIENT_EVIDENCE_MESSAGE}" '
            "and briefly explain what is missing."
        ),
        "- Keep the answer concise and grounded. Quote key phrases when useful.",
        "- Do not fabricate citations. Only reference the evidence provided.",
    ]
)


@dataclass
class ChatResult:
    """The result of a chat request: answer plus supporting citations."""

    answer: str
    citations: list
    trace: RetrievalTraceResponse
    retrieval: RetrievalResult
    answer_status: str = "answered"


def answer_question(
    question: str,
    *,
    db=None,
    doc_id: str | None = None,
    knowledge_base_id: str | None = None,
) -> ChatResult:
    """Answer a question about a document or knowledge base using evidence-first RAG.

    Pipeline (Phase 2):
        rewrite -> dense+sparse retrieval -> RRF fusion -> evidence pack -> LLM
    """
    if db is None:
        raise ValueError("db is required for Phase 2 hybrid retrieval")
    if not doc_id and not knowledge_base_id:
        raise ValueError("doc_id or knowledge_base_id is required")

    retrieval_kwargs: dict[str, str] = {}
    if doc_id is not None:
        retrieval_kwargs["doc_id"] = doc_id
    if knowledge_base_id is not None:
        retrieval_kwargs["knowledge_base_id"] = knowledge_base_id

    retrieval = run_hybrid_retrieval(db, question=question, **retrieval_kwargs)
    if not retrieval.evidence_pack:
        return ChatResult(
            answer=(
                f"{INSUFFICIENT_EVIDENCE_MESSAGE} "
                "The selected source may not be indexed yet, or retrieval returned no "
                "relevant evidence."
            ),
            citations=[],
            trace=retrieval.to_trace(question),
            retrieval=retrieval,
            answer_status="insufficient_evidence",
        )

    context = _build_context(retrieval)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{context}"},
    ]
    llm = get_llm_provider()
    answer = llm.chat(messages, temperature=0.2, max_tokens=1024)

    return ChatResult(
        answer=answer,
        citations=[item.chunk for item in retrieval.evidence_pack],
        trace=retrieval.to_trace(question),
        retrieval=retrieval,
        answer_status="answered",
    )


def _build_context(retrieval: RetrievalResult) -> str:
    """Format retrieved chunks into an evidence block for the LLM."""
    parts: list[str] = []
    for i, item in enumerate(retrieval.evidence_pack, start=1):
        chunk = item.chunk
        parts.append(f"[{i}] (page {chunk.page_start}) {chunk.text}")
    return "\n\n".join(parts)
