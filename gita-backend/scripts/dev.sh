#!/usr/bin/env bash
# Start FastAPI (uv) + Next.js together for local E2E testing.
# Usage (from repo root): ./scripts/dev.sh   or: make dev

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. See: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Node.js (npm) is required for the frontend."
  exit 1
fi

FRONTEND_PM="npm"
if command -v pnpm >/dev/null 2>&1; then
  FRONTEND_PM="pnpm"
fi

cleanup() {
  local p
  for p in $(jobs -p 2>/dev/null); do
    kill "${p}" 2>/dev/null || true
  done
}

trap cleanup INT TERM

if [[ ! -d "${ROOT}/backend/.venv" ]]; then
  echo "==> First-time setup: uv sync in backend/"
  (cd "${ROOT}/backend" && uv sync)
fi

echo "==> Backend  http://127.0.0.1:8000"
(cd "${ROOT}/backend" && exec uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000) &

if [[ ! -d "${ROOT}/gita-frontend/node_modules" ]]; then
  echo "==> Installing frontend dependencies (${FRONTEND_PM})…"
  (cd "${ROOT}/gita-frontend" && "${FRONTEND_PM}" install)
fi

echo "==> Frontend http://localhost:3000 (${FRONTEND_PM})"
(cd "${ROOT}/gita-frontend" && exec "${FRONTEND_PM}" run dev) &

wait
