"""Readiness probes for SQLite, embedding artifacts, and Ollama (sync HTTP for route handlers)."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

import httpx

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


def check_ollama_http(base_url: str, *, timeout_s: float = 3.0) -> dict[str, Any]:
    """Lightweight reachability check (Ollama ``GET /api/tags``)."""
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout_s)) as client:
            resp = client.get(url)
            resp.raise_for_status()
        return {"ok": True, "detail": None, "url": url}
    except httpx.HTTPError as exc:
        _log.debug("health_ollama_failed", extra={"url": url})
        return {"ok": False, "detail": str(exc), "url": url}
    except OSError as exc:
        return {"ok": False, "detail": str(exc), "url": url}


def build_readiness_payload(settings: Settings) -> dict[str, Any]:
    """Aggregate component checks for ``GET /health/ready``."""
    db = check_database(settings.resolved_database_path())
    emb = check_embeddings_file(settings.resolved_embeddings_npz_path())
    oll = check_ollama_http(settings.ollama_base_url, timeout_s=min(5.0, settings.ollama_connect_timeout_s + 1.0))
    overall = db["ok"] and emb["ok"] and oll["ok"]
    status = "ready" if overall else "degraded"
    return {
        "status": status,
        "components": {
            "database": db,
            "embeddings": emb,
            "ollama": oll,
        },
    }
