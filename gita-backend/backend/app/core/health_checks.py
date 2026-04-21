"""Readiness probes for SQLite, embedding artifacts, and OpenAI configuration."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.db.database import connect

_log = logging.getLogger(__name__)


def check_database(db_path: Path) -> dict[str, Any]:
    """Verify SQLite opens and answers a trivial query."""
    try:
        conn = connect(db_path)
        try:
            row = conn.execute("SELECT 1 AS ok").fetchone()
            ok = row is not None and int(row["ok"]) == 1
            verse_count: int | None = None
            if ok:
                try:
                    n = conn.execute("SELECT COUNT(*) AS n FROM verses").fetchone()
                    verse_count = int(n["n"]) if n is not None else 0
                except sqlite3.Error:
                    verse_count = None
        finally:
            conn.close()
        out: dict[str, Any] = {"ok": bool(ok), "detail": None, "path": str(db_path)}
        if verse_count is not None:
            out["verse_count"] = verse_count
        return out
    except (sqlite3.Error, OSError) as exc:
        _log.debug("health_db_failed", exc_info=True)
        return {"ok": False, "detail": str(exc), "path": str(db_path)}


def check_embeddings_file(npz_path: Path) -> dict[str, Any]:
    """Artifact optional: missing file is OK (semantic rerank disabled), corrupt is not."""
    if not npz_path.is_file():
        return {"ok": True, "detail": "artifact not present (lexical-only)", "path": str(npz_path)}
    try:
        if npz_path.stat().st_size <= 0:
            return {"ok": False, "detail": "empty artifact file", "path": str(npz_path)}
        return {"ok": True, "detail": "artifact present", "path": str(npz_path)}
    except OSError as exc:
        return {"ok": False, "detail": str(exc), "path": str(npz_path)}


def check_openai_config(settings: Settings) -> dict[str, Any]:
    """Config-only check: confirms API key + model are set.

    A network ping is intentionally avoided here so readiness does not consume credits or
    couple liveness to OpenAI uptime. Generation failures surface in the SSE error event.
    """
    key = (settings.openai_api_key or "").strip()
    model = (settings.openai_model or "").strip()
    ok = bool(key) and bool(model)
    detail = None
    if not key:
        detail = "OPENAI_API_KEY not set"
    elif not model:
        detail = "OPENAI_MODEL not set"
    return {
        "ok": ok,
        "detail": detail,
        "model": model or None,
        "base_url": settings.openai_base_url,
    }


def build_readiness_payload(settings: Settings) -> dict[str, Any]:
    """Aggregate component checks for ``GET /health/ready``."""
    db = check_database(settings.resolved_database_path())
    emb = check_embeddings_file(settings.resolved_embeddings_npz_path())
    oai = check_openai_config(settings)
    overall = db["ok"] and emb["ok"] and oai["ok"]
    status = "ready" if overall else "degraded"
    return {
        "status": status,
        "components": {
            "database": db,
            "embeddings": emb,
            "openai": oai,
        },
    }
