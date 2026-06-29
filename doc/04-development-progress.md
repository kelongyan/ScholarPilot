# ScholarPilot Development Progress

---

## Status Legend

| Status | Meaning |
|---|---|
| `Not Started` | Work has not started |
| `In Progress` | Work is currently being implemented |
| `Blocked` | Work is blocked by external dependency or decision |
| `Review` | Work is complete and waiting for review |
| `Done` | Work is accepted, committed, and pushed |

---

## Phase Status

| Phase | Name | Status | Last Updated |
|---|---|---|---|
| Phase 0 | Project Foundation | `Done` | 2026-06-29 |
| Phase 1 | Single-paper RAG MVP | `Done` | 2026-06-29 |
| Phase 2 | High-quality Hybrid RAG | `Not Started` | 2026-06-29 |
| Phase 3 | Research Workflow | `Not Started` | 2026-06-28 |
| Phase 4 | Trend Tracking and Knowledge Enhancement | `Not Started` | 2026-06-28 |
| Phase 5 | Productization and Deployment | `Not Started` | 2026-06-28 |

---

## Progress Log

### 2026-06-29 — Phase 1 complete

Implemented the single-paper RAG MVP: `Upload PDF → Parse → Chunk → Embed → Index → Retrieve → Answer → Citations`.

Backend (`backend/`):
- Data layer: SQLAlchemy 2.0 models (`Document`, `Chunk`, `Citation`) + Alembic initial migration.
- Core infra: `core/db.py` (engine/session), `core/redis.py` (Redis + RQ queue), `core/qdrant.py` (vector client + collection bootstrap).
- Providers (interface-isolated, swappable): LLM factory supports `openai` (OpenAI-compatible: Qwen/DeepSeek/local vLLM/Ollama), `anthropic` (Claude), `local`; embedding factory supports `openai` and `local` (sentence-transformers). Business code depends on `LLMProvider`/`EmbeddingProvider` protocols only.
- Services: `parser_service` (PyMuPDF, page-preserving), `chunk_service` (token-sized overlapping chunks with page provenance), `embedding_service` (batched), `vector_service` (Qdrant index/retrieve with doc_id filter), `citation_service` (evidence chain), `chat_service` (evidence-first RAG, refuses when evidence insufficient), `document_service` (upload + enqueue).
- Async: RQ worker `workers/tasks.process_document` runs parse→chunk→embed→index with status updates (`uploaded→parsing→parsed→indexing→indexed|failed`).
- API: `POST /documents/upload`, `GET /documents`, `GET /documents/{doc_id}`, `POST /documents/{doc_id}/reindex`, `POST /chat`.
- Tests: 16 tests (parser, chunk, citation unit tests; chat + documents API integration tests with mocked providers/DB). All pass.

Frontend (`frontend/`):
- Three-column workspace: document library (upload + live status polling via TanStack Query), chat panel (Q&A with selected doc), citation panel (source chunks with page/score/quote).
- `@tanstack/react-query` added. `lib/api-client.ts` + `lib/types.ts` mirror backend schemas.

Infra: root `docker-compose.yml` (PostgreSQL 16 + Qdrant + Redis 7 with persistent volumes and healthchecks).

Verification commands and results:

```text
# Backend (no external services needed for tests — providers/DB mocked)
cd backend
uv sync --extra dev                       # ok
uv run pytest                             # 16 passed
uv run ruff check                         # All checks passed
uv run python -c "from app.main import app; print(list(app.openapi()['paths']))"
# ['/health', '/documents/upload', '/documents', '/documents/{doc_id}', '/documents/{doc_id}/reindex', '/chat', '/']

# Frontend
cd frontend
pnpm install                              # ok
pnpm lint                                 # no errors
pnpm build                                # compiled successfully, TypeScript passed
pnpm dev                                  # http://localhost:3000 -> HTTP 200, three-column layout renders
```

End-to-end runtime (requires real services + API keys, not run in CI):
```text
docker compose up -d                      # postgres + qdrant + redis
cd backend && uv run alembic upgrade head # create tables
uv run uvicorn app.main:app --reload      # API on :8000
uv run rq worker --url "redis://localhost:6379/0" default   # process uploads
cd frontend && pnpm dev                   # UI on :3000
# Then: upload a PDF, wait for status=indexed, ask a question, see answer + citations.
```

Known issues / notes:
- Docker is installed but `docker` is not on the bash PATH and the Docker Desktop daemon must be started manually before `docker compose up`. Documented in backend README.
- `uv` is installed at `C:\Users\admin\AppData\Roaming\Python\Python313\Scripts\uv.exe` (not on PATH); invoke via full path.
- Alembic `--autogenerate` requires a live DB, so the initial migration was hand-written against the models.
- Tests mock providers/DB/Qdrant so they run without external services. End-to-end runtime verification with real models requires API keys in `.env`.
- Phase 1 is dense-only retrieval (no BM25/RRF/rerank — Phase 2), no query rewrite (Phase 2), no Agent workflow (Phase 3).

Commit:

```text
(filled in after commit)
```

GitHub branch:

```text
main
```

### 2026-06-29 — Phase 0 complete

- Created project foundation: backend FastAPI skeleton + frontend Next.js skeleton.
- Backend (`backend/`): FastAPI app with `GET /health` returning `{"status":"ok"}`, Pydantic Settings config (storage + LLM/embedding provider settings reserved for Phase 1), provider interface protocols (`LLMProvider`, `EmbeddingProvider`, `RerankerProvider`), pytest test suite, Ruff config, `uv.lock`, `.env.example`, README.
- Frontend (`frontend/`): Next.js App Router + TypeScript + Tailwind CSS, static three-column workspace layout (document library / reader & chat / citation panel), `lib/api-client.ts` and `lib/types.ts` skeletons, `.env.example`, README.
- Root `.gitignore` covering Python, Node, env/secrets, IDE, OS files.
- `CLAUDE.md` added for Claude Code guidance.

Verification commands and results:

```text
# Backend
cd backend
uv sync --extra dev                      # ok
uv run pytest                            # 2 passed
uv run ruff check                        # All checks passed
uv run uvicorn app.main:app --reload     # GET /health -> {"status":"ok"}

# Frontend
cd frontend
pnpm install                             # ok
pnpm lint                                # no errors
pnpm build                               # compiled successfully, TypeScript passed
pnpm dev                                 # http://localhost:3000 -> HTTP 200, three-column layout renders
```

Known issues / notes:

- `uv` was not preinstalled; installed via `pip install uv` (user site). Documented in backend README that `uv` is required.
- Docker Compose for PostgreSQL/Qdrant/Redis is deferred to Phase 1 (Phase 0 does not introduce those services, per `doc/03-technology-stack.md` §13). Connection settings are reserved in `.env.example`.
- LLM/Embedding provider interfaces are defined but not implemented; concrete adapters are Phase 1.

Commit:

```text
da3df08 feat: scaffold Phase 0 project foundation (backend + frontend)
```

GitHub branch:

```text
main
```

### 2026-06-28

- Created project planning documents.
- Established documentation organization.
- Confirmed product direction: browser-based Web Research Workspace first, desktop wrapper later if needed.
- Confirmed initial technology stack direction.

Commit:

```text
Pending
```

GitHub branch:

```text
main
```
