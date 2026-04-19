"""Append-only JSON lines for post-launch guidance feedback (opt-in via settings)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def append_guidance_feedback(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def feedback_record(
    *,
    rating: str,
    notes: str | None,
    client_stream_id: str | None,
    request_id: str | None,
) -> dict[str, Any]:
    return {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "rating": rating,
        "notes": (notes or "").strip() or None,
        "client_stream_id": (client_stream_id or "").strip() or None,
        "request_id": request_id,
    }
