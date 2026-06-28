# ScholarPilot Frontend

Next.js web UI for ScholarPilot. Phase 0 provides the application skeleton with a
static three-column workspace layout (document library / reader & chat /
citation panel). Document upload, chat, and citation features are wired up in
Phase 1.

## Requirements

- Node.js 20+
- [pnpm](https://pnpm.io/) (do **not** use npm — see project RULE.md §8.2)

## Setup

```bash
cd frontend
pnpm install
```

## Run

```bash
pnpm dev
```

Open http://localhost:3000.

## Lint and build

```bash
pnpm lint
pnpm build
```

## Configuration

Copy `.env.example` to `.env.local` and adjust the backend URL if needed:

```bash
cp .env.example .env.local
```
