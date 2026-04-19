"""Liveness and readiness endpoints (unversioned for load balancers)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_settings_dep
from app.core.config import Settings
from app.core.health_checks import build_readiness_payload

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Process liveness: returns ``{"status": "ok"}`` without touching DB or Ollama."""
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready(settings: Settings = Depends(get_settings_dep)) -> dict[str, object]:
    """
    Readiness: SQLite ping, embedding artifact presence/size, and Ollama ``GET /api/tags``.

    Use for orchestration probes. ``status`` is ``ready`` only when all components report ``ok``.

    **Example response (degraded Ollama):**

    ```json
    {
      "status": "degraded",
      "components": {
        "database": {"ok": true, "detail": null, "path": "/tmp/gita.db", "verse_count": 3},
        "embeddings": {"ok": true, "detail": "artifact not present (lexical-only)", "path": "..."},
        "ollama": {"ok": false, "detail": "...", "url": "http://127.0.0.1:11434/api/tags"}
      }
    }
    ```
    """
    return build_readiness_payload(settings)
