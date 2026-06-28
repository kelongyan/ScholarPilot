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
| Phase 1 | Single-paper RAG MVP | `Not Started` | 2026-06-29 |
| Phase 2 | High-quality Hybrid RAG | `Not Started` | 2026-06-28 |
| Phase 3 | Research Workflow | `Not Started` | 2026-06-28 |
| Phase 4 | Trend Tracking and Knowledge Enhancement | `Not Started` | 2026-06-28 |
| Phase 5 | Productization and Deployment | `Not Started` | 2026-06-28 |

---

## Progress Log

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
(filled in after commit)
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
