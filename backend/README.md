# Kairos Backend

FastAPI backend for Kairos, a verifiable team knowledge-base Q&A and knowledge
operations platform. The backend handles document ingestion, parsing, chunking,
embedding, Hybrid RAG retrieval, evidence-backed answers, citations, and trace
data.

The current implemented path is:

```
Upload source document → Parse → Chunk → Embed → Index → Hybrid Retrieve → Answer → Citations + Trace
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management
- [Docker](https://www.docker.com/) (for PostgreSQL, Qdrant, Redis)

## Setup

### 1. Start infrastructure

```bash
# From the repo root
docker compose up -d
docker compose ps   # wait until postgres/qdrant/redis are healthy
```

### 2. Install backend dependencies

```bash
cd backend
uv sync --extra dev
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in at least:
- `LLM_API_KEY` (and `LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_MODEL` if not using OpenAI)
- `EMBEDDING_API_KEY` (and `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` if not using OpenAI)

Provider options:
- `LLM_PROVIDER=openai` — OpenAI or any OpenAI-compatible endpoint (Qwen, DeepSeek, local vLLM/Ollama via `LLM_BASE_URL`)
- `LLM_PROVIDER=anthropic` — Anthropic Claude
- `LLM_PROVIDER=local` — local model via OpenAI-compatible endpoint
- `EMBEDDING_PROVIDER=openai` — OpenAI-compatible embeddings
- `EMBEDDING_PROVIDER=local` — local sentence-transformers (install with `uv sync --extra local`)

### 4. Run database migrations

```bash
uv run alembic upgrade head
```

## Run

### API server

```bash
uv run uvicorn app.main:app --reload
```

The API is served at http://localhost:8000.

- Health check: http://localhost:8000/health
- Interactive docs: http://localhost:8000/docs

### RQ worker (processes uploaded PDFs)

In a separate terminal:

```bash
uv run rq worker --url "redis://localhost:6379/0" default
```

The worker picks up document processing jobs (parse → chunk → embed → index).
Without it, uploads stay in `uploaded` status.

## Test

```bash
uv run pytest
```

Tests use mocked providers (no real LLM/embedding/DB/Qdrant needed).

## Lint and format

```bash
uv run ruff check
uv run ruff format
```

## Architecture

```
app/
├─ api/            # HTTP routes (documents, chat, health)
├─ schemas/        # Pydantic DTOs
├─ services/       # Business orchestration (parser, chunk, embedding, vector, chat, citation, document)
├─ repositories/   # Data access (PostgreSQL)
├─ models/         # SQLAlchemy ORM models
├─ providers/      # External capability adapters (LLM, embedding) behind interfaces
├─ workers/        # RQ async tasks
├─ core/           # Config, db, redis, qdrant
└─ main.py         # FastAPI app
```

Dependency direction (RULE.md §5.3): `api → services → repositories`,
`services → providers`. Business code depends on provider interfaces, never
on a concrete SDK.
