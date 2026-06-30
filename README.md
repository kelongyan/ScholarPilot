# Kairos

Kairos is being repositioned as a verifiable team knowledge-base Q&A and knowledge operations platform.

The project turns internal documents into searchable, traceable, and evaluable knowledge assets:

```text
Upload documents
  -> Parse
  -> Chunk
  -> Embed / Index
  -> Hybrid Retrieval
  -> Evidence Pack
  -> Grounded Answer
  -> Citations + Feedback + Trace
  -> Knowledge Gap Discovery
```

The earlier “AI Research Copilot for paper reading” direction is now treated as one vertical scenario, not the main product line. Controlled Multi-Agent workflows remain a later capability, not the short-term product promise.

---

## Current Direction

```text
Next.js Web UI
  -> FastAPI Backend
  -> PostgreSQL / Qdrant / Redis
  -> Document Pipeline / Hybrid RAG / Feedback / Trace
  -> Knowledge Operations
  -> Controlled Multi-Agent Workflow (later)
  -> LLM / Embedding / Reranker Providers
```

The current implementation now contains the core single-document RAG and the knowledge-base layer. The next product phase is to add knowledge operations, trace persistence, evaluation, and access control.

---

## Documentation

Read the documents in this order:

| Order | Document | Purpose |
|---|---|---|
| 1 | [RULE.md](RULE.md) | Project rules, development constraints, Git rules, testing requirements |
| 2 | [doc/00-product-requirements.md](doc/00-product-requirements.md) | New product requirements baseline |
| 3 | [doc/01-project-overview.md](doc/01-project-overview.md) | Product positioning, architecture, current baseline |
| 4 | [doc/02-development-roadmap.md](doc/02-development-roadmap.md) | Phased development plan and acceptance criteria |
| 5 | [doc/03-technology-stack.md](doc/03-technology-stack.md) | Technology choices and adoption rules |
| 6 | [doc/04-development-progress.md](doc/04-development-progress.md) | Current status and progress log |
| 7 | [doc/05-environment-setup.md](doc/05-environment-setup.md) | Local development environment |
| 8 | [doc/06-local-llm-deployment.md](doc/06-local-llm-deployment.md) | Local model deployment notes |

---

## Repository Structure

```text
Kairos/
├─ backend/       # FastAPI backend, RAG services, workers, providers
├─ frontend/      # Next.js UI
├─ doc/           # Product, roadmap, tech stack, progress, environment docs
├─ scripts/       # Local setup and helper scripts
├─ README.md
└─ RULE.md
```

---

## Technology Summary

```text
Frontend:
Next.js + React + TypeScript + pnpm + Tailwind CSS + TanStack Query

Backend:
Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic + uv + Ruff + Pytest

Storage:
PostgreSQL + Qdrant + Redis + local filesystem

RAG:
Qdrant dense retrieval + BM25 sparse retrieval + RRF + reranker boundary + Evidence Pack

Future:
Knowledge base layer -> feedback/knowledge gaps -> auth/RBAC/trace persistence -> controlled Multi-Agent workflows
```

Tooling policy:

```text
Short term: keep the current stack stable and build the knowledge-base layer plus basic feedback and knowledge-gap tracking.
Mid term: add trace persistence, RAG evaluation, real reranker providers, and controlled LangGraph workflows.
Long term: evaluate Docling, Langfuse/Phoenix, LiteLLM, OpenSearch/Elasticsearch, Milvus, MCP, A2A, and GraphRAG only when concrete bottlenecks appear.
```

---

## Phase Status

| Phase | Goal | Current Status |
|---|---|---|
| Phase 0 | Engineering foundation | `Done` |
| Phase 1 | Core RAG loop | `Done` |
| Phase 2 | Hybrid RAG and trace engine | `Done` |
| Phase 3 | Knowledge base product layer | `Done` |
| Phase 4 | Knowledge operations, auth, audit, evaluation, observability | `In Progress` |
| Phase 5 | Multi-Agent orchestration | `Not Started` |
| Phase 6 | Production, dashboard, extensions | `Not Started` |

Current priority:

```text
Start Phase 4 knowledge operations, trace persistence, and access control
```

---

## Implemented Highlights

- FastAPI + Next.js project foundation.
- PostgreSQL metadata models for documents, chunks, and citations.
- PDF upload, parsing, chunking, embedding, indexing, and status tracking.
- Redis/RQ worker pipeline.
- Qdrant dense retrieval.
- BM25 sparse retrieval, RRF fusion, reranker provider boundary.
- Evidence Pack and retrieval trace returned by `/chat`.
- Frontend document list, chat panel, citation panel, and trace summary.

Not implemented yet:

- Multi-format ingestion beyond PDF.
- Knowledge gap tracking and richer operations views.
- User auth, RBAC, audit logs.
- Trace persistence and evaluation API.
- Multi-Agent orchestration.

---

## Development Rules

Before development:

- Read [RULE.md](RULE.md).
- Follow the product baseline in [doc/00-product-requirements.md](doc/00-product-requirements.md).
- Follow the roadmap in [doc/02-development-roadmap.md](doc/02-development-roadmap.md).
- Update [doc/04-development-progress.md](doc/04-development-progress.md) when phase status changes.

Each completed phase must be implemented, verified, documented, committed, and pushed.

---

## GitHub

Repository:

```text
https://github.com/kelongyan/Kairos
```
