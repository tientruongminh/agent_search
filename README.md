# Agentic Material Search V2

Monorepo baseline for a production-oriented material discovery system with:

- `apps/api`: FastAPI API, orchestration, verification, ranking, packaging, Dramatiq worker
- `apps/web`: Next.js polling UI for search jobs and results
- `docs`: architecture diagram, OpenAPI outline, ranking profiles, source policies

## Quick start

1. Copy `.env.example` to `.env` and fill the keys you have.
2. Start the stack:

```bash
docker compose up --build
```

3. Open:

- API: `http://localhost:8000`
- Web: `http://localhost:3000`

## Included baseline

- Async search jobs with persisted job state and events
- OpenAI-backed intent and query planning with deterministic fallback
- Brave, GitHub, and page-crawler retrieval channels
- Guardrailed downloader and verification pipeline
- Goal-aware ranking and artifact packaging
- Simple single-tenant UI for submitting jobs and downloading results

## Notes

- The system is intentionally write-first for feedback memory. Online learning is deferred.
- Local disk is the default storage backend; S3 mirror support is available via config.
- Web search and LLM calls degrade gracefully to deterministic fallback when credentials are missing.

