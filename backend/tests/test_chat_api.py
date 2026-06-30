"""Integration tests for the chat API with mocked providers.

These tests verify the RAG orchestration end-to-end without depending on a
real LLM, embedding service, Qdrant, or PostgreSQL. Providers and the vector
store are monkeypatched.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app
from app.services.retrieval_service import RetrievalResult, RetrievedEvidence
from app.services.vector_service import RetrievedChunk

client = TestClient(app)


def _fake_get_db():
    """Yield a dummy object; the chat route's DB is unused once get_document is mocked."""
    yield object()


def _setup_db_override() -> None:
    app.dependency_overrides[get_db] = _fake_get_db


def _teardown_db_override() -> None:
    app.dependency_overrides.pop(get_db, None)


def _fake_retrieved() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id="chunk-1",
            doc_id="doc-1",
            text="The model uses a cross-encoder reranker.",
            section="Method",
            page_start=3,
            page_end=3,
            chunk_type="paragraph",
            chunk_index=0,
            score=0.91,
        )
    ]


def _fake_question_log():
    class FakeQuestionLog:
        question_log_id = "ql-1"

    return FakeQuestionLog()


def test_chat_returns_answer_and_citations(monkeypatch) -> None:
    """``POST /chat`` returns an answer grounded in retrieved evidence."""
    from app.repositories import document_repo
    from app.services import chat_service, chat_trace_service, question_log_service

    class FakeDoc:
        status = "indexed"

    monkeypatch.setattr(document_repo, "get_document", lambda db, doc_id: FakeDoc())

    evidence = RetrievedEvidence(chunk=_fake_retrieved()[0], retrieval_source="dense")
    monkeypatch.setattr(
        chat_service,
        "run_hybrid_retrieval",
        lambda db, doc_id, question: RetrievalResult(
            rewritten_query=question,
            dense_results=[],
            sparse_results=[],
            fused_results=[evidence],
            reranked_results=[evidence],
            evidence_pack=[evidence],
        ),
    )

    class FakeLLM:
        def chat(self, messages, **kwargs):
            return "The model uses a cross-encoder reranker."

    monkeypatch.setattr(chat_service, "get_llm_provider", lambda: FakeLLM())
    monkeypatch.setattr(
        question_log_service,
        "create_question_log",
        lambda *args, **kwargs: _fake_question_log(),
    )
    monkeypatch.setattr(
        chat_trace_service,
        "create_chat_trace",
        lambda *args, **kwargs: None,
    )

    _setup_db_override()
    try:
        response = client.post(
            "/chat", json={"doc_id": "doc-1", "question": "What reranker is used?"}
        )
    finally:
        _teardown_db_override()

    assert response.status_code == 200
    body = response.json()
    assert "reranker" in body["answer"]
    assert len(body["citations"]) == 1
    cite = body["citations"][0]
    assert cite["doc_id"] == "doc-1"
    assert cite["page"] == 3
    assert cite["score"] == 0.91
    assert "reranker" in cite["quote"]
    assert body["trace"]["rewritten_query"] == "What reranker is used?"
    assert body["question_log_id"] == "ql-1"


def test_chat_rejects_non_indexed_document(monkeypatch) -> None:
    """``POST /chat`` returns 409 when the document is not yet indexed."""
    from app.repositories import document_repo

    class FakeDoc:
        status = "indexing"

    monkeypatch.setattr(document_repo, "get_document", lambda db, doc_id: FakeDoc())

    _setup_db_override()
    try:
        response = client.post(
            "/chat", json={"doc_id": "doc-1", "question": "anything"}
        )
    finally:
        _teardown_db_override()

    assert response.status_code == 409


def test_chat_returns_404_for_missing_document(monkeypatch) -> None:
    """``POST /chat`` returns 404 when the document does not exist."""
    from app.repositories import document_repo

    monkeypatch.setattr(document_repo, "get_document", lambda db, doc_id: None)

    _setup_db_override()
    try:
        response = client.post(
            "/chat", json={"doc_id": "missing", "question": "anything"}
        )
    finally:
        _teardown_db_override()

    assert response.status_code == 404


def test_chat_handles_no_evidence(monkeypatch) -> None:
    """When retrieval returns nothing, the answer states evidence is insufficient."""
    from app.repositories import document_repo
    from app.services import chat_service, chat_trace_service, question_log_service

    class FakeDoc:
        status = "indexed"

    monkeypatch.setattr(document_repo, "get_document", lambda db, doc_id: FakeDoc())
    monkeypatch.setattr(
        chat_service,
        "run_hybrid_retrieval",
        lambda db, doc_id, question: RetrievalResult(
            rewritten_query=question,
            dense_results=[],
            sparse_results=[],
            fused_results=[],
            reranked_results=[],
            evidence_pack=[],
        ),
    )
    monkeypatch.setattr(
        question_log_service,
        "create_question_log",
        lambda *args, **kwargs: _fake_question_log(),
    )
    monkeypatch.setattr(
        chat_trace_service,
        "create_chat_trace",
        lambda *args, **kwargs: None,
    )

    _setup_db_override()
    try:
        response = client.post(
            "/chat", json={"doc_id": "doc-1", "question": "anything"}
        )
    finally:
        _teardown_db_override()

    assert response.status_code == 200
    body = response.json()
    assert "Insufficient evidence" in body["answer"]
    assert body["citations"] == []
    assert body["trace"]["evidence_pack"] == []
    assert body["question_log_id"] == "ql-1"


def test_chat_supports_knowledge_base_scope(monkeypatch) -> None:
    """``POST /chat`` supports knowledge-base-level questions."""
    from app.repositories import knowledge_base_repo
    from app.services import chat_service, chat_trace_service, question_log_service

    class FakeKB:
        knowledge_base_id = "kb-1"

    monkeypatch.setattr(
        knowledge_base_repo, "get_knowledge_base", lambda db, kb: FakeKB()
    )

    evidence = RetrievedEvidence(chunk=_fake_retrieved()[0], retrieval_source="dense")
    monkeypatch.setattr(
        chat_service,
        "run_hybrid_retrieval",
        lambda db, question, knowledge_base_id=None, doc_id=None: RetrievalResult(
            rewritten_query=question,
            dense_results=[],
            sparse_results=[],
            fused_results=[evidence],
            reranked_results=[evidence],
            evidence_pack=[evidence],
        ),
    )

    class FakeLLM:
        def chat(self, messages, **kwargs):
            return "The model uses a cross-encoder reranker."

    monkeypatch.setattr(chat_service, "get_llm_provider", lambda: FakeLLM())
    monkeypatch.setattr(
        question_log_service,
        "create_question_log",
        lambda *args, **kwargs: _fake_question_log(),
    )
    monkeypatch.setattr(
        chat_trace_service,
        "create_chat_trace",
        lambda *args, **kwargs: None,
    )

    _setup_db_override()
    try:
        response = client.post(
            "/chat",
            json={"knowledge_base_id": "kb-1", "question": "What reranker is used?"},
        )
    finally:
        _teardown_db_override()

    assert response.status_code == 200
    body = response.json()
    assert body["citations"][0]["doc_id"] == "doc-1"
    assert body["question_log_id"] == "ql-1"
