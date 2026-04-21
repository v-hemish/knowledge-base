# Gita guidance backend

A **retrieval-first** HTTP API for Bhagavad Gita–style guidance: users ask in natural language; the service finds relevant verses in a **local SQLite corpus**, optionally reranks them with **precomputed embeddings**, and may attach a **streamed explanation** from **OpenAI**. Verse text shown to clients is **always** loaded from the database—never invented or rewritten by the model.

This repository layout assumes you work from the **`backend/`** directory (where this file, `pyproject.toml`, `Makefile`, and the `app/` package live).

---

## What this backend does

1. **Ingest** normalized verse records (translation, optional Sanskrit/transliteration, tags, provenance) into SQLite with **FTS5** full-text search.
2. **Retrieve** candidate verses using lexical search, then optionally **cosine-rerank** with sentence-transformer embeddings loaded from a local **`.npz`** artifact.
3. **Expose** two guidance modes:
   - **Retrieve only** — JSON with verse cards and deterministic “why selected” lines (no LLM).
   - **Stream** — Server-Sent Events (SSE): verse cards first, then tokenized explanation text from OpenAI, with structured errors and a short fallback if generation fails or times out.
4. **Evaluate** retrieval quality offline against a small JSON eval suite (citation hit rates, misleading retrieval, etc.).

---

## Product principles

These align with project guardrails for scripture-adjacent products:

| Principle | Practice in this codebase |
|-----------|---------------------------|
| **Retrieval before generation** | Verses are chosen by the retrieval pipeline; the LLM only sees retrieved verses in its prompt. |
| **Canonical text from the DB** | API verse payloads are assembled from SQLite rows; the model is not used to paraphrase or “fix” verse text. |
| **Not a generic chatbot** | Endpoints are scoped to guidance + debug retrieval; prompts emphasize grounding in the supplied verses. |
| **Local-first MVP** | FastAPI, SQLite, optional local embeddings file — no Redis, Postgres, Kafka, Celery, or hosted vector DB in scope. The single hosted dependency is OpenAI for explanation generation; verse retrieval is fully local. |
| **Careful tone** | Prompts and copy avoid performative persona; explanations are framed as reflection on the cited text. |
| **Small, testable modules** | Retrieval, LLM client, schemas, and services are separated; behavior changes should come with tests where practical. |

---

## Architecture overview

```text
Client
  │
  ├─► POST /api/v1/guidance/retrieve  ──► AnswerAssemblerService
  │                                         └── RetrievalPipelineService
  │                                               ├── Lexical (FTS5 / BM25)
  │                                               └── Optional cosine rerank (NPZ embeddings)
  │
  ├─► POST /api/v1/guidance/stream    ──► stream_guidance_events
  │                                         ├── same retrieval path
  │                                         └── OpenAI (HTTP SSE) + deadlines / fallback
  │
  └─► GET  /health, /health/ready      ──► liveness vs DB + artifact + OpenAI config probes
```

- **SQLite** is the source of truth for verse content and metadata.
- **Embeddings** are optional: if `verses_embeddings.npz` is missing or invalid, the API falls back to lexical ordering (when semantic rerank is enabled but no artifact, startup logs a warning).
- **OpenAI** is required for a live **stream** explanation. `/api/v1/guidance/retrieve` works without it. Readiness checks report component status without blocking liveness; the OpenAI probe is config-only (key + model present) so readiness does not consume credits.

---

## Folder structure

```text
backend/
├── README.md                 ← you are here
├── Makefile                  ← install, run, test, data + embedding tasks
├── pyproject.toml            ← package metadata, deps, pytest / ruff config
├── .env.example              ← documented environment variables
├── app/                      ← installable Python package
│   ├── main.py               ← FastAPI app factory, lifespan, exception handlers
│   ├── api/                  ← HTTP routers, dependencies
│   │   ├── deps.py           ← settings, DB connection, rate limiting
│   │   └── routes/
│   │       ├── health.py     ← /health, /health/ready
│   │       └── v1/           ← versioned API (guidance, retrieval, version)
│   ├── core/                 ← settings, logging, paths, health checks, rate limit
│   ├── middleware/           ← request ID middleware
│   ├── db/                   ← SQLite connection, schema, migrations, ingestion, ORM helpers
│   ├── models/               ← domain types (e.g. Verse)
│   ├── schemas/              ← Pydantic request/response and ingest documents
│   ├── retrieval/            ← FTS search, pipeline, rerank, embedding store + artifact I/O
│   ├── services/             ← orchestration (guidance stream, assembler, lexical debug)
│   ├── llm/                  ← OpenAI HTTP client, prompts, polish, validation
│   ├── evals/                ← eval schema, metrics, runner (used by scripts)
│   └── utils/                ← SSE helpers, etc.
├── data/                     ← sample corpus, review query JSON (not secrets)
│   ├── canonical_sample.json
│   ├── guidance_review_queries.json
│   └── (generated captures like guidance_model_review*.json — gitignored)
├── scripts/                  ← CLI entrypoints (ingest, seed, embed, eval)
└── tests/                    ← pytest suite
```

---

## Setup instructions

**Requirements:** **[uv](https://docs.astral.sh/uv/getting-started/installation/)** on your `PATH`. Python version follows **`backend/.python-version`** (currently **3.12**); uv can download that runtime if missing (`uv python install 3.12`).

From **`backend/`**:

```bash
uv sync
cp .env.example .env
# Edit .env to set OPENAI_API_KEY and adjust paths/limits if needed.
```

`uv sync` creates **`.venv/`**, installs the package in editable mode, and includes the **dev** dependency group (pytest). Equivalent Makefile shortcuts:

| Command | Purpose |
|---------|---------|
| `make sync` or `make install` | `uv sync` |
| `make run` | `uv run uvicorn …` |
| `make test` | `uv run pytest` |
| `make load-sample-data` | Seed sample corpus |
| `make build-embeddings` | Build NPZ artifact |
| `make dev` | Start **API + Next.js** together (runs `../scripts/dev.sh`; same as `make dev` from the **parent** repo folder) |

**Lockfile:** commit **`uv.lock`** once generated (`uv sync` writes it). CI and teammates get reproducible installs.

**Manual equivalents (no Make):**

```bash
uv sync
uv run pytest -q
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Troubleshooting

- **`uv sync` / resolver errors:** run **`uv lock --upgrade`** after dependency bumps, or pin a working Python with **`uv python pin 3.12`**.
- **Stale or broken venv:** **`rm -rf .venv`** then **`uv sync`** again.
- **Full stack (API + Next.js) from repo root:** see **`../README.md`** → `make dev`.

---

## Environment variables

All variables are optional unless you need non-default behavior. Values are read via **pydantic-settings** (environment and optional `.env` in the process working directory).

| Variable | Purpose |
|----------|---------|
| `APP_NAME` | FastAPI title metadata. |
| `ENVIRONMENT` | Logical name (e.g. `development`); used in logs. |
| `LOG_LEVEL` | Root log level (`INFO`, `DEBUG`, …). |
| `DATA_DIR` | Directory for default SQLite DB and default embedding artifact paths. |
| `DATABASE_PATH` | Override SQLite file path (otherwise `DATA_DIR/gita.db`). |
| `FTS_CANDIDATE_LIMIT` | Max lexical candidates before rerank (capped in settings). |
| `FINAL_VERSE_COUNT` | Verses returned to the client (upper bound enforced in config). |
| `EMBEDDING_MODEL` | Model id used by `scripts/embed_verses.py` (default BGE-small). |
| `EMBEDDINGS_ARTIFACT_PATH` | Override path to `verses_embeddings.npz`. |
| `SEMANTIC_RERANK_ENABLED` | When `true`, rerank uses NPZ if present; otherwise lexical order. |
| `OPENAI_API_KEY` | **Required for `/guidance/stream`.** Lives in `.env` (gitignored). |
| `OPENAI_MODEL` | OpenAI model id (default `gpt-5-mini`; `gpt-4o-mini` also supported). |
| `OPENAI_BASE_URL` | OpenAI base URL (override for compatible proxies). |
| `OPENAI_MAX_COMPLETION_TOKENS` | Decode cap. On reasoning models (`gpt-5*`, `o1`, `o3`, `o4`) this also covers internal reasoning tokens. |
| `OPENAI_TEMPERATURE` / `OPENAI_TOP_P` | Decoding controls (silently dropped for reasoning models that mandate defaults). |
| `OPENAI_CONNECT_TIMEOUT_S` / `OPENAI_READ_TIMEOUT_S` / `OPENAI_WRITE_TIMEOUT_S` | httpx timeouts for OpenAI streams. |
| `OPENAI_GENERATION_DEADLINE_S` | Wall-clock cap per streamed explanation (asyncio timeout). |
| `GUIDANCE_RATE_LIMIT_PER_MINUTE` | Per-IP sliding window for **stream** and **feedback** (`0` disables). |
| `GUIDANCE_RETRIEVE_RATE_LIMIT_PER_MINUTE` | Separate cap for **POST /guidance/retrieve** only (default higher; `0` disables). |
| `RETRIEVE_CACHE_MAX_ENTRIES` / `RETRIEVE_CACHE_TTL_S` | In-process cache for identical retrieve-only requests (`0` max entries disables). |

A full commented template lives in **`.env.example`**.

---

## How to load canonical verse data

**Option A — sample corpus (fastest for local dev)**

```bash
make load-sample-data
# runs: uv run python scripts/seed_database.py
```

Seeds from `data/canonical_sample.json` into the database path implied by your settings.

**Option B — arbitrary canonical JSON file**

From `backend/`, with a path **under this tree** if you use a relative path (scripts resolve relative paths against `backend/` for safety):

```bash
uv run python scripts/load_verses.py data/canonical_sample.json
# optional DB override:
uv run python scripts/load_verses.py data/canonical_sample.json --database ./data/custom.db
```

The loader expects the canonical schema validated in `app/schemas/verse_document.py` (normalized verse objects). After ingest, FTS is updated as part of the ingestion path.

---

## How to build embeddings

Precompute embeddings for **all verses currently in the database** and write:

- `verses_embeddings.npz` (+ companion metadata) under `DATA_DIR` by default, or next to your configured paths.

```bash
make build-embeddings
# runs: uv run python scripts/embed_verses.py
```

This uses **sentence-transformers** locally (first run may download the model). For custom DB/output:

```bash
uv run python scripts/embed_verses.py --database ./data/gita.db --output ./data/verses_embeddings.npz
```

Restart the API after rebuilding so the in-memory index reloads from disk.

---

## How to run the API

```bash
make run
# uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or explicitly:

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **OpenAPI / docs:** `http://127.0.0.1:8000/docs` (Swagger UI) when `ENVIRONMENT` is suitable for exposing docs.
- **OpenAI** key must be set in `.env` for live streamed explanations; `/health/ready` reports `degraded` if it is missing.

---

## How to run tests

```bash
make test
```

Or:

```bash
uv run pytest
```

Tests assume the package is importable (editable install or `pythonpath` from `pyproject.toml` when running from `backend/`). Use **`-q`** or **`-k pattern`** for faster iteration during development.

---

## Endpoint overview

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness: process is up. |
| `GET` | `/health/ready` | Readiness: SQLite ping, embedding artifact check, OpenAI config presence. |
| `GET` | `/api/v1/version` | API version + installed package version. |
| `POST` | `/api/v1/guidance/retrieve` | JSON: selected verses + deterministic “why selected” text; **no** LLM. |
| `POST` | `/api/v1/guidance/stream` | SSE: `metadata` → `verses` → `token` chunks → optional `error` + fallback `token` → `completed`. |
| `GET` | `/api/v1/retrieval/lexical` | Debug: BM25 lexical hits (`q` query param). Intended for development; **restrict or remove** before public exposure. |

Request bodies for guidance endpoints use **`{"query": "<non-empty string>"}`** (max length enforced in schema). Responses use structured JSON; SSE lines are `data: <json>` per event. Clients should send or read **`X-Request-ID`** for supportability ( echoed on responses and included in logs).

---

## Benchmarking the generation backend

Polish, validation, and fallback are model-agnostic, so swapping the OpenAI model is a single
env flip. Capture two runs over the same eval queries to compare.

```bash
# Capture against the current default model (e.g. gpt-5-mini)
.venv/bin/python scripts/capture_guidance_eval_run.py --debug \
  --out data/guidance_model_review_openai_gpt5mini.json

# Switch model and re-capture
export OPENAI_MODEL=gpt-4o-mini
# restart uvicorn so settings reload (lru_cache holds a snapshot per process)
.venv/bin/python scripts/capture_guidance_eval_run.py --debug \
  --out data/guidance_model_review_openai_gpt4omini.json
```

Both captures share identical retrieval results and identical polish/validate contracts; only
the model differs. The SSE `metadata` event carries the active `model` string so eval files
are unambiguous when diffed.

---

## Evaluation philosophy

Offline evaluation focuses on **retrieval correctness**, not on scoring LLM prose (which would need separate human rubrics).

- **Suite format:** JSON cases with a user query and **acceptable / misleading** citation keys (`tests/fixtures/eval_cases.json`).
- **Runner:** `scripts/run_eval.py` loads the suite, runs the **same** `retrieve_verses_for_query` path used in production, and aggregates metrics (e.g. citation hit rate, top-1 / top-3, misleading retrieval rate). See `app/evals/metrics.py` for definitions.
- **Intent:** Catch regressions when changing lexical tuning, rerank weights, or corpus ingest—before shipping UI or prompt changes.

```bash
uv run python scripts/run_eval.py
uv run python scripts/run_eval.py --suite tests/fixtures/eval_cases.json --database ./data/gita.db
```

---

## MVP boundaries

In scope for this MVP:

- Single-tenant, single-process assumptions for **in-memory** rate limiting and retrieve caching.
- **English-centric** retrieval and embedding defaults; corpus content is whatever you load.
- **Local** retrieval, embeddings, and SQLite — only generation is hosted (OpenAI).
- **SQLite + FTS5** as the only database; no sync replicas or migration to Postgres in-tree.

Out of scope (unless added deliberately later):

- User accounts, OAuth, API keys, org billing.
- Distributed tracing, centralized log aggregation, metrics backends.
- Vector databases, message queues, or job runners for ingest.
- Licensing or ingestion of full copyrighted translations without your own rights clearance.

---

## Known limitations

- **Retrieve cache** does not invalidate when the database changes in-process; restart the server or lower TTL / disable caching after bulk reloads.
- **Rate limiting** is per server process and typically by observed client IP; it is not a substitute for edge rate limiting or auth in production.
- **Readiness** treats OpenAI config presence as part of “full stack healthy”; `/guidance/retrieve` still works without an OpenAI key, but `/health/ready` reports `degraded`.
- **Evals** measure retrieval citations, not explanation faithfulness or theological adequacy.
- **Debug lexical endpoint** can leak retrieval behavior; do not expose it publicly without gating.
- **Path rules in scripts:** some CLI paths must resolve under `backend/` when relative—see script `--help` and `app/core/paths.py` for expectations.

---

## Next steps

Reasonable follow-ons before or during frontend integration:

1. **Contract hardening** — Publish a short SSE client spec (event order, error vs fallback, reconnection) and pin OpenAPI for the frontend code generator.
2. **CORS** — Configure allowed origins when the UI is served from another host.
3. **Auth and abuse controls** — If the API leaves localhost: API keys or JWT, stricter rate limits at the edge, request size caps.
4. **Corpus expansion** — Ingest pipeline for a fully licensed translation; chapter/verse integrity checks and content hashing.
5. **Observability** — Metrics (latency histograms, OpenAI error rate) and trace IDs beyond JSON request logs.
6. **Embedding lifecycle** — Version NPZ with schema migrations so rerank never silently mismatches verse rows.

For engineering conventions and non-negotiables around verse text and LLM use, see **`AGENTS.md`** wherever your repository keeps project rules (often beside this `backend/` directory).

---

## License

Project licensing is defined by the parent repository; this package does **not** ship a full licensed Gita translation—only sample or user-supplied data.
