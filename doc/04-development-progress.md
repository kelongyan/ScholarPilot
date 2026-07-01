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
P4 知识运营清单持久化、第一版审计日志、固定 QA 评测 API 和最小 auth/RBAC 边界已启动。
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
| Source document upload | Done | PDF, Markdown, TXT, HTML, and DOCX baseline |
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
| Multi-format ingestion | Done | Stage 4 parser dispatch supports PDF, Markdown, TXT, HTML, and DOCX |
| Document lifecycle | Done | Version replacement, archive, restore, delete, audit, and index cleanup |
| User auth and RBAC | In progress | Bearer token/JWT auth, KB-scope filtering, frontend role-gated controls, and persisted KB memberships started |
| Audit logs | In progress | `audit_logs` table, filtered API, frontend panel, and key event capture including evaluation events started |
| Evaluation runs | In progress | Fixed QA dataset, persisted chat/agent runs, dataset/config snapshots, richer quality metrics, artifact links, and frontend panel implemented |
| SSE streaming | Not started | Future chat enhancement |
| Multi-Agent workflow | In progress | Controlled workflow API, persisted step trace, run review UI, filters, and operations list started in Phase 5 |
| Dashboard | In progress | Stage 2 observability summary, trend, regression alerts, latency buckets, and frontend panel implemented |

---

## 5. Progress Log

### 2026-07-01 - Stage 4 closeout

Closed Product closure Stage 4: Document Lifecycle Loop for the current in-repo implementation.

Implemented in this iteration:

- Added document lifecycle fields with Alembic migration `c8d9e0f1a2b3_add_document_lifecycle_fields.py`.
- Added `content_hash`, `version`, `lifecycle_status`, `replaces_doc_id`, and `replaced_by_doc_id` to documents.
- Added document lifecycle APIs:
  - `POST /documents/{doc_id}/replace`
  - `POST /documents/{doc_id}/archive`
  - `POST /documents/{doc_id}/restore`
  - `DELETE /documents/{doc_id}`
- Replacement now creates a new active version, archives the previous version, and records the version chain.
- Archive/delete retire old PostgreSQL chunks and Qdrant vectors; restore requeues indexing.
- KB-level sparse retrieval and failed-document operation signals now ignore non-active documents.
- Direct chat, Agent, evaluation, and reindex entry points now reject non-active documents.
- Frontend source list now supports replace, archive, restore, and delete actions with version/lifecycle display.
- Added lifecycle service/API tests for replacement, archive, restore, delete, requeue, and index cleanup behavior.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 101 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed
.\.venv\Scripts\python.exe -m alembic upgrade head
# upgraded b7c8d9e0f1a2 -> c8d9e0f1a2b3
.\.venv\Scripts\python.exe -m alembic current
# c8d9e0f1a2b3 (head)

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Stage 4 status: complete for the current lightweight ingestion and lifecycle implementation.

Deferred beyond this stage:

- OCR and layout-rich parsing for complex scanned PDFs, tables, and slides.
- Content-level duplicate clustering beyond stored content hashes.
- Hard-delete physical file cleanup policy, once retention requirements are defined.

---

### 2026-07-01 - Stage 4 multi-format ingestion started

Started Product closure Stage 4: Document Lifecycle Loop with the first multi-format ingestion slice.

Implemented in this iteration:

- Added parser dispatch with normalized source types for `pdf`, `markdown`, `text`, `html`, and `docx`.
- Kept PDF parsing on PyMuPDF and added lightweight standard-library parsers for Markdown/TXT, HTML, and DOCX.
- Changed document upload validation from PDF-only to the supported source set: PDF, Markdown, TXT, HTML, DOCX.
- Updated document persistence so uploaded files record their detected `source`.
- Updated the worker to parse by `Document.source` before chunking, embedding, and indexing.
- Updated the frontend upload control to accept the supported formats and show source type in the source list.
- Added parser/API tests for text, HTML, DOCX, unsupported upload rejection, and TXT upload acceptance.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 95 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Stage 4 follow-up status: closed by the 2026-07-01 Stage 4 closeout entry above.

---

### 2026-07-01 - Stage 3 closeout

Closed Product closure Stage 3: Permissions and Governance Loop for the current in-repo product slice.

Implemented in this iteration:

- Added frontend knowledge-base member management UI with member listing and role/status upsert.
- Mounted the member management panel in the main workspace for management-capable users.
- Corrected governance route permissions:
  - Listing KB members requires `manager`.
  - Creating or updating KB members requires `owner`.
- Tightened membership-aware access rules so configured KB memberships take precedence over legacy JWT KB scope. Existing KBs without configured members still fall back to the previous scope/static-role behavior.
- Added test coverage for owner-only member upsert, legacy scope fallback, and membership precedence over claim scope.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 91 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed
.\.venv\Scripts\python.exe -m alembic heads
# b7c8d9e0f1a2 (head)
.\.venv\Scripts\python.exe -m alembic current
# b7c8d9e0f1a2 (head)

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Stage 3 status: complete for the current KB-membership governance implementation.

Deferred beyond this stage:

- Organization/workspace tenant models, if cross-KB tenant boundaries become a real product need.
- Invite/email flows and richer member lifecycle UX beyond direct member role/status management.
- External policy engine integration such as Casbin/OpenFGA, unless role rules outgrow the current local matrix.

---

### 2026-07-01 — Stage 3 governance memberships started

Started Product closure Stage 3: Permissions and Governance Loop.

Implemented in this iteration:

- Added persisted `user_accounts` and `knowledge_base_members` governance models.
- Added Alembic migration `b7c8d9e0f1a2_add_governance_memberships.py`.
- Added governance repository, service, schemas, and `/governance` API routes:
  - `GET /governance/users/me`
  - `GET /governance/knowledge-bases/{knowledge_base_id}/members`
  - `PUT /governance/knowledge-bases/{knowledge_base_id}/members/{user_id}`
- Creating a knowledge base now creates an owner membership for the actor and records a member audit event.
- Added membership-aware permission helpers with roles `viewer`, `contributor`, `manager`, and `owner`.
- Connected membership-aware access checks to knowledge-base, document, chat, Agent, evaluation, observability, trace, question-log, and knowledge-operation entry points.
- Added frontend API client/type support for governance user and KB member APIs.
- Kept backward compatibility: existing KBs without configured members still fall back to the previous JWT scope/static-role behavior.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 90 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed
.\.venv\Scripts\python.exe -m alembic heads
# b7c8d9e0f1a2 (head)
.\.venv\Scripts\python.exe -m alembic upgrade head
# upgraded a7b8c9d0e1f2 -> b7c8d9e0f1a2
.\.venv\Scripts\python.exe -m alembic current
# b7c8d9e0f1a2 (head)

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Stage 3 follow-up status: closed by the 2026-07-01 Stage 3 closeout entry above.

---

### 2026-07-01 — Stage 2 closeout

Closed Product closure Stage 2: Evaluation and Observability Loop.

Implemented in this iteration:

- Added `dataset_version` and `config_snapshot_json` to evaluation runs with Alembic migration `a7b8c9d0e1f2`.
- Stored a stable dataset hash plus retrieval, reranker, chunking, LLM, embedding, execution, app version, and cost-placeholder config snapshot per run.
- Expanded per-item evaluation metrics with deterministic proxies for Recall@K, MRR, citation accuracy, citation coverage, faithfulness, answer relevance, retrieval hit counts, citation support, estimated tokens, and cost placeholder.
- Expanded run-level metrics and deltas for the new quality dimensions.
- Extended observability summary with evaluation trend points, regression alerts, and trace latency buckets.
- Updated frontend Evaluation and Observability panels to show the new metrics, trends, and alerts.
- Added auth-enabled smoke coverage for KB manager observability access and denied cross-KB trace access.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 85 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed
.\.venv\Scripts\python.exe -m alembic heads
# a7b8c9d0e1f2 (head)
.\.venv\Scripts\python.exe -m alembic upgrade head
# upgraded f6a7b8c9d0e1 -> a7b8c9d0e1f2
.\.venv\Scripts\python.exe -m alembic current
# a7b8c9d0e1f2 (head)

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Stage 2 remaining item status: complete for the in-repo deterministic implementation. Future upgrades can replace proxy metrics with Ragas/DeepEval or trace-platform metrics once the self-owned metrics surface becomes insufficient.

---

### 2026-07-01 — Stage 2 artifact drill-down and observability summary

Continued Product closure Stage 2 by connecting evaluation results to their review artifacts and adding a first management-view observability slice.

Implemented in this iteration:

- Added KB-scoped single chat trace access for knowledge-base managers, while keeping the full trace list admin-only.
- Added frontend drill-down actions from evaluation items:
  - `Trace` loads the persisted chat trace into the right-side evidence panel.
  - `Agent` loads the persisted Agent run with citations, retrieval trace, and step trace.
- Added `GET /observability/summary` for current quality and backlog signals.
- Aggregated latest evaluation quality, question/no-answer rate, negative feedback rate, persisted trace latency, pending operation backlog, high-severity backlog, and operation signal count.
- Added a compact Observability panel scoped to the selected knowledge base.
- Added backend service/API tests for observability aggregation and trace scope lookup.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 81 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Remaining Stage 2 work:

- Add dataset/config version snapshots to evaluation runs.
- Add richer retrieval/citation metrics such as Recall@K, MRR, citation accuracy, faithfulness, and answer relevance.
- Add auth-enabled smoke verification for admin, KB manager, and user tokens.

---

### 2026-07-01 — Stage 2 evaluation run comparison

Continued Stage 2 by making evaluation results comparable across runs.

Implemented in this iteration:

- Added previous-run lookup for the same dataset, knowledge-base/document scope, and execution mode.
- Added `previous_run_id` and `metric_deltas` to evaluation run responses.
- Calculated deltas for pass rate, average keyword coverage, answer rate, trace rate, error rate, average answer length, average latency, and max latency.
- Updated the Evaluations panel to show pass, coverage, and latency deltas against the previous comparable run.
- Added tests for deterministic metric delta calculation and API response compatibility.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 77 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

---

### 2026-07-01 — Stage 1 closeout and Stage 2 evaluation metrics

Closed the remaining Stage 1 knowledge-operations gap and started Stage 2 from `doc/07-product-closure-plan.md`.

Stage 1 closeout implemented:

- Added `knowledge_operation_drafts` for draft FAQ/source-material records created while handling operation items.
- Changed `document_added` handling from a manual status only into a real draft-creation action.
- Reused an existing draft for the same operation item when present, avoiding duplicate draft records.
- Recorded draft creation/reuse details in the operation handling event.
- Added `GET /knowledge-operations/drafts` with filters for knowledge base, operation item, and status.

Stage 2 started with evaluation observability metrics:

- Added `metrics_json` to evaluation runs and run items.
- Added per-question metrics: keyword coverage, answer presence, trace presence, answer length, latency, and error flag.
- Added run-level metrics: average keyword coverage, answer rate, trace rate, error rate, average answer length, average latency, and max latency.
- Exposed evaluation metrics in API responses and the frontend Evaluations panel.
- Kept the implementation deterministic and in-repo; no external evaluation framework introduced yet.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 76 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed
.\.venv\Scripts\python.exe -m alembic upgrade head
# upgraded e5f6a7b8c9d0 -> f6a7b8c9d0e1
.\.venv\Scripts\python.exe -m alembic current
# f6a7b8c9d0e1 (head)

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

---

### 2026-06-30 — Product closure Stage 1 operation history and grouping

Continued Stage 1 from `doc/07-product-closure-plan.md` by closing more of the knowledge operations loop.

Implemented in this iteration:

- Added `knowledge_operation_events` as structured lifecycle history for operation items.
- Added `aggregate_key`, `signal_count`, and `last_signal_at` to operation items.
- Recorded generated quality signals as `signal_detected` events.
- Recorded handling actions as `status_updated` events with actor id, previous status, target status, notes, and action details.
- Aggregated repeated no-answer and feedback signals into a single pending operation item while preserving each original signal as an event.
- Kept failed-document and Agent-run items source-specific so document reindexing and run-scoped review links remain precise.
- Added `GET /knowledge-operations/items/{item_id}/events`.
- Updated the Operations panel with work-type filtering for knowledge gaps, answer quality, citation review, failed documents, and Agent warnings.
- Added signal counts, latest signal timestamps, and expandable history in the operation item cards.
- Added backend service/API coverage for aggregation, event history, and update history.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 73 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed
.\.venv\Scripts\python.exe -m alembic heads
# e5f6a7b8c9d0 (head)

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Remaining Stage 1 item: completed on 2026-07-01.

---

### 2026-06-30 — Product closure Stage 1 operation reindex action

Started Stage 1 from `doc/07-product-closure-plan.md`: knowledge operations should trigger real remediation, not only mark status.

Implemented in this iteration:

- Updated knowledge operation handling so `reindexed` calls the document reindex service before the operation item is marked handled.
- Added conflict handling for invalid remediation cases, including operation items without a document id and missing source documents.
- Changed the operation item update API to load the item and check knowledge-base access before executing any handling action.
- Appended the system action result into `resolution_note` so the handling trail records that reindexing was queued.
- Updated the Operations panel action label to `Queue reindex`, only shows it for document-backed items, refreshes documents/audit/operation data after success, and surfaces update errors in the panel.
- Added backend API and service tests for reindex execution and conflict behavior.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 71 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

---

### 2026-06-30 — Phase 4 minimal auth/RBAC

Continued P4 closeout by adding the first coarse-grained authentication and authorization boundary.

Implemented in this iteration:

- Added `app.core.auth` with disabled-by-default development mode, static Bearer role tokens, and HS256 JWT claim parsing.
- Added `/auth/me` to expose current actor, role, auth mode, and optional knowledge-base scope.
- Added RBAC roles: `user`, `kb_manager`, and `admin`.
- Protected management and observability routes:
  - `user`: knowledge-base/document read, chat, feedback, dataset read.
  - `kb_manager`: uploads, reindex, Agent runs, evaluation runs, operations handling.
  - `admin`: audit logs, chat traces, question log review, unrestricted KB scope.
- Added knowledge-base scope checks and filtering for scoped JWTs with `knowledge_base_ids` or `kb_ids`.
- Updated audit events to use the authenticated actor id where available.
- Added frontend auth token forwarding via `NEXT_PUBLIC_KAIROS_AUTH_TOKEN`.
- Added frontend role-gated controls for knowledge-base creation, upload, Agent mode/history, operations, evaluations, and audit logs.
- Updated backend and frontend `.env.example` files with auth configuration knobs.
- Added auth API tests for disabled dev mode, missing token behavior, role denial, admin access, and KB-scope filtering.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m pytest
# 64 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed
.\.venv\Scripts\python.exe -m alembic heads
# c3d4e5f6a7b8 (head)
.\.venv\Scripts\python.exe -m alembic current
# c3d4e5f6a7b8 (head)

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

Commit:

```text
1099397 feat: add minimal auth rbac
```

---

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

### 2026-06-30 — Phase 5 Agent operations closure

Continued Phase 5 by closing the Agent-to-operations loop with persisted linkage and UI entry points.

Implemented in this iteration:

- Added `agent_run_id` to `knowledge_operation_items` plus a new Alembic migration and foreign key to `agent_runs`.
- Added best-effort Agent run sync inside `agent_service.create_agent_run()`.
- Added `source_type` and `source_id` filtering to persisted knowledge operation item listing.
- Added `run_id` support to `/knowledge-operations/suggestions` so a specific Agent run can surface its operation item.
- Added frontend source-type filtering for operations, including `agent_run`.
- Added a run-scoped operations entry point from Agent history and a clear-filter affordance in the operations panel.
- Added backend service/API coverage for Agent-run sync, deduplication, filtering, and suggestion lookup.

Verification recorded:

```text
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
# upgraded c3d4e5f6a7b8 -> d4e5f6a7b8c9
.\.venv\Scripts\python.exe -m pytest
# 68 passed, 1 warning
.\.venv\Scripts\python.exe -m ruff check
# All checks passed

cd frontend
pnpm lint
# ok
pnpm build
# compiled successfully
```

---

## 6. Next Recommended Implementation Phase

Next phase:

```text
Product closure Stage 5: Retrieval and Answer Quality Loop
```

Recommended next tasks:

1. Add stronger citation/evidence validation before answer generation.
2. Improve insufficient-evidence gating so weak retrieval results refuse more reliably.
3. Add retrieval quality diagnostics per query, including low-confidence and conflicting-evidence signals.
4. Introduce a real reranker provider only after the deterministic baseline metrics show a bottleneck.
5. Add regression tests for archived/deleted document exclusion in dense and sparse retrieval.
