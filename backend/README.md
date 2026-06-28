# ScholarPilot Backend

FastAPI backend for ScholarPilot. Phase 0 provides the application skeleton and
a health check endpoint. RAG functionality (document parsing, embedding,
retrieval, chat) is added in Phase 1.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management

## Setup

```bash
cd backend
uv sync --extra dev
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

The API is served at http://localhost:8000.

- Health check: http://localhost:8000/health
- Interactive docs: http://localhost:8000/docs

## Test

```bash
uv run pytest
```

## Lint and format

```bash
uv run ruff check
uv run ruff format
```

## Configuration

Copy `.env.example` to `.env` and fill in the values. The storage and model
settings are reserved for Phase 1; Phase 0 does not connect to any external
service.

```bash
cp .env.example .env
```
