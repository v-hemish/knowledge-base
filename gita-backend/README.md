# Gita backend + frontend (monorepo)

| Path | Role |
|------|------|
| `backend/` | FastAPI API (managed with **[uv](https://docs.astral.sh/uv/)**) |
| `gita-frontend/` | Next.js test UI |

## One command: API + UI

From **`gita-backend/`** (this folder):

```bash
make dev
```

This runs **`bash scripts/dev.sh`**: starts **uvicorn** on **http://127.0.0.1:8000** and **Next.js** on **http://localhost:3000**. **Ctrl+C** stops both.

**Prerequisites**

1. **[uv](https://docs.astral.sh/uv/getting-started/installation/)** installed and on `PATH`.
2. **Node.js** (includes `npm`). **pnpm** is used automatically if installed.

First run creates `backend/.venv` via `uv sync` and installs frontend `node_modules` if missing.

## Backend only

```bash
cd backend
uv sync
cp .env.example .env
uv run python scripts/seed_database.py
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

See **`backend/README.md`** for architecture, env vars, retrieval eval, and the guidance review sample.

## Frontend only

```bash
cd gita-frontend
cp .env.local.example .env.local
pnpm install && pnpm dev
# or: npm install && npm run dev
```

See **`gita-frontend/README.md`** for CORS vs proxy and env vars.
