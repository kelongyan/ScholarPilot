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
核心 RAG 引擎、知识库产品层和基础 trace 持久化已建立；
Phase 5 受控 Agent 工作流、Agent run 过滤和确定性知识运营建议已启动；
P4 知识运营清单持久化、第一版审计日志和固定 QA 评测 API 已启动，权限/RBAC 仍待补齐。
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
| Phase 3 | Knowledge Base Product Layer | `Done` | 2026-06-30 |
| Phase 4 | Knowledge Operations, Auth, Audit, Evaluation, Observability | `In Progress` | 2026-06-30 |
| Phase 5 | Multi-Agent Orchestration | `In Progress` | 2026-06-30 |
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
| Retrieval trace | In progress | Returned by `/chat`; persistence started in Phase 4 |
| Knowledge base entity | Done | Phase 3 |
| Knowledge-base-level QA | Done | Phase 3 |
| User feedback | Done | Phase 3 |
| Knowledge gap tracking | In progress | Persisted operation items from no-answer logs, poor feedback, and failed documents |
| Multi-format ingestion | Not started | PDF only |
| User auth and RBAC | Not started | Phase 4 |
| Audit logs | In progress | `audit_logs` table, filtered API, frontend panel, and key event capture including evaluation events started |
| Evaluation runs | In progress | Fixed QA dataset, persisted chat/agent runs, result items, artifact links, and frontend panel implemented |
| SSE streaming | Not started | Future chat enhancement |
| Multi-Agent workflow | In progress | Controlled workflow API, persisted step trace, run review UI, filters, and operations list started in Phase 5 |
| Dashboard | Not started | Phase 6 |

---

## 5. Progress Log

### 2026-06-30 — Phase 4 evaluation runs

Continued P4 closeout by adding the first repeatable evaluation API and review UI.

Implemented in this iteration:

- Added `evaluation_datasets`, `evaluation_runs`, and `evaluation_run_items` ORM models and Alembic migration.
- Added repository, schema, service, and `/evaluations` API routes for dataset listing/detail, run creation, run listing, and run detail.
- Seeded the default `phase2_fixed_qa` dataset from `backend/tests/fixtures/phase2_eval_questions.csv`.
- Added synchronous chat/agent evaluation execution with deterministic keyword matching, pass/fail counts, average latency, answer status counts, and route counts.
- Persisted per-question links to question logs, chat traces, and Agent runs where available.
- Added scope validation for knowledge-base and document evaluation runs.
- Added best-effort audit events for evaluation run creation and detail review.
- Added a frontend Evaluations panel scoped to the selected knowledge base.
- Added backend API/service tests and frontend API/types support.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 59 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed
.\.venv\Scripts\python.exe -m alembic heads
# c3d4e5f6a7b8 (head)
.\.venv\Scripts\python.exe -m alembic upgrade head
# upgraded b2c3d4e5f6a7 -> c3d4e5f6a7b8

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Commit:

```text
09dfd6c feat: add evaluation runs
```

---

### 2026-06-30 — Phase 4 audit logs

Continued Phase 4 closeout by adding the first persisted audit-log slice.

Implemented in this iteration:

- Added `audit_logs` ORM model and Alembic migration.
- Added repository, service, schema, and `GET /audit-logs` API with filters for knowledge base, action, resource, actor, and date range.
- Recorded audit events for document upload, document reindex, feedback submission, Agent run creation, Agent run detail review, and knowledge operation item status updates.
- Kept audit writes best-effort so a logging failure does not break the primary workflow.
- Added a frontend Audit Logs panel scoped to the selected knowledge base.
- Changed Agent run selection to load the detail endpoint so review actions are audit logged.
- Added API and service tests for audit log filtering, serialization, persistence calls, and best-effort failure handling.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 52 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed
.\.venv\Scripts\python.exe -m alembic heads
# b2c3d4e5f6a7 (head)
.\.venv\Scripts\python.exe -m alembic upgrade head
# upgraded a1d2e3f4b5c6 -> b2c3d4e5f6a7

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Commit:

```text
5a27f94 feat: add audit logs
```

---

### 2026-06-30 — Phase 4 knowledge operations item persistence

Continued Phase 4 closeout by turning generated knowledge operation suggestions into persisted actionable items.

Implemented in this iteration:

- Added `knowledge_operation_items` ORM model and Alembic migration.
- Added repository, service, schema, and API support for persisted operation items.
- `GET /knowledge-operations/items` now syncs missing generated signals into persisted items before listing them.
- `PATCH /knowledge-operations/items/{item_id}` updates handling status and resolution notes.
- Supported statuses: `pending`, `resolved`, `ignored`, `reindexed`, and `document_added`.
- Kept `/knowledge-operations/suggestions` as a backward-compatible pending-suggestion view backed by persisted items.
- Updated the frontend Operations panel with status filtering and item handling buttons.
- Added API and service tests for item sync, deduplication, status updates, and 404 behavior.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 48 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Commit:

```text
ac2acb7 feat: persist knowledge operation items
```

---

### 2026-06-30 — Phase 5 deterministic knowledge operations suggestions

Continued Phase 5 and P4 closeout by adding a deterministic Knowledge Operations suggestion slice.

Implemented in this iteration:

- Added `/knowledge-operations/suggestions` API.
- Added knowledge operations schemas and service.
- Generated pending suggestions from existing signals:
  - no-answer or insufficient-evidence question logs,
  - not-useful or citation-inaccurate feedback,
  - failed document parsing/indexing status.
- Added frontend knowledge operations panel scoped to the selected knowledge base.
- Feedback submission now invalidates knowledge operation suggestions so poor feedback appears in the operations loop.
- Added service and API tests for generated suggestions and knowledge-base filtering.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 46 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Commit:

```text
4553294 feat: add agent run filters and operations suggestions
```

---

### 2026-06-30 — Phase 5 Agent run filters

Continued Phase 5 by adding filtered Agent run review and resolving the current-priority documentation conflict.

Implemented in this iteration:

- Updated `RULE.md` current priority from the completed Phase 3 knowledge-base layer to Phase 5 controlled Agent workflows plus Phase 4 closeout.
- Added `/agent-runs` filters for `knowledge_base_id`, `route`, `status`, `answer_status`, `created_from`, and `created_to`.
- Persisted the document's `knowledge_base_id` on document-scoped Agent runs so knowledge-base filtering includes runs launched from a selected source.
- Added frontend Agent run filters for current knowledge base, route, run status, answer status, and date range.
- Added API test coverage to verify Agent run list filters are passed through.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 46 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Commit:

```text
4553294 feat: add agent run filters and operations suggestions
```

---

### 2026-06-30 — Phase 5 Agent run review UI

Continued Phase 5 by exposing persisted Agent runs in the workspace UI.

Implemented in this iteration:

- Added frontend API client methods for `/agent-runs` list and detail.
- Added shared frontend type for `AgentRunListResponse`.
- Added Agent run history panel showing recent route, status, latency, step count, citation count, and question.
- Selecting a persisted Agent run now loads its citations, retrieval trace, and Agent step trace into the right-hand review panel.
- Agent mode responses now invalidate the Agent run history query so new runs appear without a page reload.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 42 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully

Runtime check:
GET http://127.0.0.1:3000
# 200
GET http://127.0.0.1:8000/agent-runs
# returned persisted Agent runs
```

Commit:

```text
bcc0e4a feat: add Agent run history review
```

---

### 2026-06-30 — Phase 5 started

Started the controlled Multi-Agent orchestration phase with a bounded first slice.

Implemented in this iteration:

- Added persisted `agent_runs` and `agent_steps` models plus Alembic migration.
- Added controlled Agent workflow service with planner, retrieval, analyst, writer, and reviewer steps.
- Added automatic route selection: direct questions use the short route, analytical questions use the multi-agent route.
- Added max-step enforcement and failure exit behavior.
- Added `/agent-runs` create/list/detail API routes.
- Reused the existing evidence-first RAG answer path so Agent outputs retain citations and retrieval trace.
- Added frontend Chat/Agent mode selection and Agent step trace display.
- Added tests for routing, max-step behavior, persistence serialization, and API routes.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 42 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully

WSL:
docker compose up -d
# postgres/qdrant/redis healthy

cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
# upgraded through 9b7a6c3d2e1f_add_agent_runs

Runtime verification:
- Restarted backend after Qdrant was healthy; previous Qdrant version warning no longer appears.
- Windows backend verified with local Ollama at `LLM_BASE_URL=http://127.0.0.1:11434/v1` and model `qwen3:14b`.
- Windows RQ worker still cannot process jobs because RQ uses `os.fork`; WSL worker is required.
- Uploaded a PDF into a test knowledge base.
- Processed indexing with WSL worker: document status `indexed`, page_count=1.
- `/chat` returned citations=1, trace evidence=1, and a persisted question log.
- `/agent-runs` selected `multi_agent`, completed 5 steps, returned citations=1, and persisted step trace.
```

Commit:

```text
68f74cd feat: start Phase 5 controlled agents
```

---

### 2026-06-30 — Phase 4 started

Started the Knowledge Operations, Auth, Audit, Evaluation, and Observability phase.

Implemented in this iteration:

- Added persisted chat trace model, migration, repository, service, and API routes.
- Added `/chat-traces` list and detail endpoints.
- Extended `/chat` to persist retrieval trace artifacts after a question log is created.
- Persisted query, rewritten query, dense/sparse/fused/reranked results, Evidence Pack, answer, citations, status, model placeholder, and latency placeholder.
- Added tests for chat trace serialization and trace API routes.

Verification recorded:

```text
cd backend
uv run python -m pytest
# 35 passed, 1 warning
uv run python -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Commit:

```text
97eaf0c feat: start Phase 4 trace persistence
```

---

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

### 2026-06-30 — Phase 3 complete

Completed the Knowledge Base Product Layer.

Implemented in this iteration:

- Added `KnowledgeBase` ORM model and Alembic migration.
- Added `knowledge_base_id` to documents and Qdrant payloads.
- Added knowledge base repository, schemas, service, and API routes.
- Added knowledge-base-aware document upload and list filtering.
- Added knowledge-base-scoped hybrid retrieval and chat support while preserving `doc_id` compatibility.
- Added frontend knowledge base selection, creation, scoped upload, filtered document list, and KB-level chat fallback.
- Added question logs and minimal answer feedback.
- Added tests for knowledge base CRUD, filtered document listing, scoped upload, KB-level chat, and feedback logging.

Verification recorded:

```text
cd backend
uv run python -m pytest
# 29 passed, 1 warning
uv run python -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Commit:

```text
f8b9aa7 feat: complete Phase 3 knowledge base layer
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
Phase 5: Multi-Agent Orchestration
```

Recommended next tasks:

1. Apply the new `evaluation_*` migration in any database that has not run `c3d4e5f6a7b8`.
2. Run an end-to-end evaluation against an indexed knowledge base and verify the Evaluations and Audit Logs panels show the run.
3. Add minimal auth/RBAC boundaries for administrators, knowledge-base managers, and users.
4. Add richer evaluation metrics or dashboard views only after fixed QA runs are stable in real data.
5. Decide whether the current in-repo Agent state machine should be replaced by LangGraph after P5 contracts stabilize.
