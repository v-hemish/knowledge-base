import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_guidance_feedback_disabled_by_default() -> None:
    client = TestClient(create_app())
    r = client.post(
        "/api/v1/guidance/feedback",
        json={"rating": "down", "notes": "awkward ending"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("accepted") is False
    assert body.get("reason") == "feedback_logging_disabled"


def test_guidance_feedback_appends_jsonl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("GUIDANCE_FEEDBACK_LOG_PATH", "guidance_feedback.jsonl")
    get_settings.cache_clear()

    client = TestClient(create_app())
    r = client.post(
        "/api/v1/guidance/feedback",
        json={"rating": "flag", "notes": "truncated", "client_stream_id": "abc-1"},
        headers={"X-Request-ID": "req-xyz"},
    )
    assert r.status_code == 200
    assert r.json().get("accepted") is True

    logf = tmp_path / "guidance_feedback.jsonl"
    assert logf.is_file()
    line = logf.read_text(encoding="utf-8").strip().splitlines()[-1]
    rec = json.loads(line)
    assert rec["rating"] == "flag"
    assert rec["notes"] == "truncated"
    assert rec["client_stream_id"] == "abc-1"
    assert rec["request_id"] == "req-xyz"
    assert rec["received_at"]
