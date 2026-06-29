# Kairos Development Progress

---

## 1. 当前产品基线

2026-06-29 起，Kairos 的主产品定位调整为：

```text
可验证的团队知识库问答与知识运营平台
```

原有“论文阅读、证据检索与科研分析 Copilot”定位降级为垂直场景。Multi-Agent 不作为短期主卖点，而作为后期受控工作流能力。后续进度统计和路线图以 `doc/00-product-requirements.md`、`doc/01-project-overview.md`、`doc/02-development-roadmap.md` 为准。

当前代码状态判断：

```text
核心 RAG 引擎已基本跑通；
知识库产品层和知识运营闭环尚未建立。
```

---

## 2. Status Legend

| Status | Meaning |
|---|---|
| `Not Started` | Work has not started |
| `In Progress` | Work is currently being implemented |
| `Review` | Work is complete and waiting for verification, docs sync, commit, or push |
| `Done` | Work is accepted, committed, and pushed |
| `Blocked` | Work is blocked by dependency or decision |

---

## 3. Phase Status

| Phase | Name | Status | Last Updated |
|---|---|---|---|
| Phase 0 | Engineering Foundation | `Done` | 2026-06-29 |
| Phase 1 | Core RAG Loop | `Done` | 2026-06-29 |
| Phase 2 | Hybrid RAG and Trace Engine | `Done` | 2026-06-29 |
| Phase 3 | Knowledge Base Product Layer | `Not Started` | 2026-06-29 |
| Phase 4 | Knowledge Operations, Auth, Audit, Evaluation, Observability | `Not Started` | 2026-06-29 |
| Phase 5 | Multi-Agent Orchestration | `Not Started` | 2026-06-29 |
| Phase 6 | Production, Dashboard, Extensions | `Not Started` | 2026-06-29 |

---

## 4. Capability Matrix

| Capability | Current Status | Notes |
|---|---|---|
| FastAPI backend | Implemented | Active backend in `backend/app` |
| Next.js frontend | Implemented | Three-column workspace |
| PostgreSQL models | Implemented | Document, Chunk, Citation |
| PDF upload | Implemented | PDF only |
| PDF parsing | Implemented | PyMuPDF, page-preserving |
| Chunking | Implemented | Token-sized overlap chunks |
| Embedding and Qdrant indexing | Implemented | Provider-isolated |
| Dense retrieval | Implemented | Qdrant |
| BM25 sparse retrieval | Implemented | `rank-bm25`, stopword-filtered lexical matches |
| RRF fusion | Implemented | Phase 2 code |
| Reranker provider boundary | Implemented | deterministic fallback only |
| Evidence Pack | Implemented | Returned in trace |
| Retrieval trace | Implemented | Returned by `/chat`, not persisted |
| Knowledge base entity | Not started | Next phase |
| Knowledge-base-level QA | Not started | Next phase |
| User feedback | Not started | Next phase |
| Knowledge gap tracking | Not started | Phase 3/4 |
| Multi-format ingestion | Not started | PDF only |
| User auth and RBAC | Not started | Phase 4 |
| Audit logs | Not started | Phase 4 |
| SSE streaming | Not started | Future chat enhancement |
| Multi-Agent workflow | Not started | Phase 5 |
| Dashboard | Not started | Phase 6 |

---

## 5. Progress Log

### 2026-06-29 — Product reposition and documentation baseline

Product direction changed from “AI Research Copilot” to “verifiable team knowledge-base Q&A and knowledge operations platform”.

Documentation update scope:

- Added `doc/00-product-requirements.md` as the new product requirements baseline.
- Rewrote `doc/01-project-overview.md` around the knowledge-base Q&A and knowledge operations direction.
- Rewrote `doc/02-development-roadmap.md` to map current implementation to the new phase plan.
- Rewrote `doc/03-technology-stack.md` to keep the existing stack while adding knowledge base, auth, trace, evaluation, and Agent requirements.
- Rebuilt this progress file so future status reflects the new product line.

Important decision:

- Do not discard the existing RAG work.
- Treat the current implementation as the RAG foundation for the new product.
- Next implementation phase should be Knowledge Base Product Layer plus minimal feedback/knowledge-gap signals, not Multi-Agent.
- Technology adoption should remain staged: do not introduce LangGraph, Docling, Langfuse/Phoenix, LiteLLM, OpenSearch, Milvus, MCP, A2A, or GraphRAG until their triggering conditions are met.

Technology stack update:

- Short term: keep FastAPI, Next.js, PostgreSQL, Qdrant, Redis/RQ, current RAG pipeline, and provider abstraction.
- Phase 3: focus on `KnowledgeBase`, document ownership, multi-document retrieval, knowledge-base-level chat, basic feedback, and question logging.
- Phase 4: add knowledge operations lists, minimal JWT/RBAC, audit logs, trace persistence, and RAG evaluation; Ragas/DeepEval can be introduced after fixed eval data exists.
- Phase 5: introduce LangGraph only for controlled Agent workflows.
- Phase 6+: evaluate Docling, Unstructured, MarkItDown, Langfuse/Phoenix, LiteLLM, OpenSearch/Elasticsearch, Milvus, Casbin/OpenFGA, MCP, A2A, and GraphRAG based on concrete bottlenecks.

Commit:

```text
43ee5b5 feat: align project with Kairos direction
```

---

### 2026-06-29 — Phase 2 complete

Implemented the first complete Hybrid RAG loop on top of the Phase 1 single-document MVP:

```text
query rewrite
  -> dense retrieval + BM25 sparse retrieval
  -> RRF fusion
  -> rerank
  -> Evidence Pack
  -> answer + citations + retrieval trace
```

Backend:

- Added `query_service`, `sparse_retrieval_service`, `retrieval_service`, and `rag` schemas.
- Added deterministic query rewrite seam.
- Added BM25 sparse retrieval over indexed chunk text.
- Added RRF fusion of dense and sparse results.
- Added swappable reranker provider boundary and deterministic fallback reranker.
- Fixed BM25 sparse retrieval so lexical matches are preserved even when raw BM25 scores are non-positive.
- `/chat` now returns structured retrieval trace while preserving answer and citations.
- Added `SPARSE_RETRIEVAL_TOP_K`, `RERANK_TOP_K`, and `RERANKER_PROVIDER`.
- Added minimal Phase 2 evaluation fixture.

Frontend:

- Header shows `Phase 2 · Hybrid RAG`.
- Chat panel forwards trace metadata.
- Citation panel displays query, rewritten query, stage hit counts, and Evidence Pack details.

Verification recorded:

```text
cd backend
uv run python -m pytest
# 24 passed, 1 warning
uv run python -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Runtime verification recorded:

```text
WSL:
docker compose up -d
# postgres/qdrant/redis healthy

Windows backend:
uv run python -m alembic upgrade head
uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/health
# {"status":"ok"}

WSL worker:
.venv-wsl/bin/python -m rq.cli worker --burst --url "redis://localhost:6379/0" default
# process_document completed successfully

Runtime chat verification:
POST /documents/upload
# status uploaded
GET /documents/{doc_id}
# status indexed, page_count 4
POST /chat
# answer grounded in evidence
# citations=4
# dense_results=4
# sparse_results=4
# fused_results=4
# reranked_results=4
# evidence_pack=4
```

Known gaps:

- Retrieval trace is not persisted.
- Reranker fallback is not a model-based cross-encoder.
- Evidence Pack is not a dedicated database artifact.
- Scope remains single-document `doc_id`, not knowledge-base-level retrieval.

Commit:

```text
fix: complete Phase 2 runtime verification
```

---

### 2026-06-29 — Phase 1 complete

Implemented the single-document RAG MVP:

```text
Upload PDF -> Parse -> Chunk -> Embed -> Index -> Retrieve -> Answer -> Citations
```

Backend:

- SQLAlchemy models: `Document`, `Chunk`, `Citation`.
- Alembic initial migration.
- DB, Redis/RQ, and Qdrant core infrastructure.
- Provider abstraction for LLM and embedding providers.
- Services for parser, chunking, embedding, vector indexing, citation, chat, and document upload.
- RQ worker processes parse/chunk/embed/index status flow.
- APIs: `POST /documents/upload`, `GET /documents`, `GET /documents/{doc_id}`, `POST /documents/{doc_id}/reindex`, `POST /chat`.

Frontend:

- Document library with upload and status polling.
- Chat panel for selected document.
- Citation panel for source chunks.
- TanStack Query integration.

Verification recorded:

```text
cd backend
uv run pytest
# 16 passed
uv run ruff check
# All checks passed

cd frontend
pnpm lint
# no errors
pnpm build
# compiled successfully
```

Commit:

```text
a2d0b5e feat: implement Phase 1 single-paper RAG MVP
```

---

### 2026-06-29 — Phase 0 complete

Created project foundation:

- FastAPI backend skeleton.
- Next.js frontend skeleton.
- Health check endpoint.
- Pydantic settings.
- Provider protocol boundaries.
- Pytest and Ruff configuration.
- Basic frontend layout.
- Project documentation and development rules.

Verification recorded:

```text
cd backend
uv run pytest
# 2 passed
uv run ruff check
# All checks passed

cd frontend
pnpm lint
# no errors
pnpm build
# compiled successfully
```

Commit:

```text
da3df08 feat: scaffold Phase 0 project foundation (backend + frontend)
```

---

## 6. Next Recommended Implementation Phase

Next phase:

```text
Phase 3: Knowledge Base Product Layer
```

Recommended first tasks:

1. Add `KnowledgeBase` ORM model and Alembic migration.
2. Add `knowledge_base_id` to documents.
3. Add knowledge base repository, schemas, and API routes.
4. Update upload API to require or default a knowledge base.
5. Extend retrieval to accept `knowledge_base_id` and search all indexed documents in that scope.
6. Extend `/chat` to support knowledge-base-level question answering while keeping `doc_id` compatibility.
7. Record questions, answers, citations, evidence-insufficient cases, and basic user feedback.
8. Update frontend to show knowledge bases, group documents, and collect minimal feedback.
9. Add backend tests for knowledge base CRUD, document ownership, retrieval scope, and feedback recording.

Do not start Multi-Agent implementation before this phase is stable.
