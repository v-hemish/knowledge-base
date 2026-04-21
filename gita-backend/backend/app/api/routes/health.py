"""Liveness and readiness endpoints (unversioned for load balancers)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_settings_dep
from app.core.config import Settings
from app.core.health_checks import build_readiness_payload

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Process liveness: returns ``{"status": "ok"}`` without touching DB or OpenAI."""
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready(settings: Settings = Depends(get_settings_dep)) -> dict[str, object]:
    """
    Readiness: SQLite ping, embedding artifact presence/size, and OpenAI config presence.

    Use for orchestration probes. ``status`` is ``ready`` only when all components report ``ok``.
    The OpenAI check is config-only (key + model) — we do not call the API on each probe.

    **Example response (degraded OpenAI config):**

    ```json
    {
      "status": "degraded",
      "components": {
        "database": {"ok": true, "detail": null, "path": "/tmp/gita.db", "verse_count": 3},
        "embeddings": {"ok": true, "detail": "artifact not present (lexical-only)", "path": "..."},
        "openai": {"ok": false, "detail": "OPENAI_API_KEY not set", "model": "gpt-5-mini", "base_url": "https://api.openai.com/v1"}
      }
    }
    ```
    """
    return build_readiness_payload(settings)
