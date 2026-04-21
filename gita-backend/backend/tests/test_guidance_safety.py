"""Timeouts, rate limits, retrieve cache, and generation fallback behavior."""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import connect, init_schema
from app.db.ingestion import ingest_verse_inputs
from app.db.session import make_engine, make_session_factory, session_scope
from app.main import create_app
from app.services.retrieval_pipeline_service import RetrievalPipelineService


def test_guidance_stream_deadline_emits_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    make_verse_input,
) -> None:
    """Wall-clock ``OPENAI_GENERATION_DEADLINE_S`` cancels a hung generation stream."""
    db = tmp_path / "deadline.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    # Settings floor is 5s; sleep longer than deadline so asyncio.timeout fires.
    monkeypatch.setenv("OPENAI_GENERATION_DEADLINE_S", "5")
    get_settings.cache_clear()

    init_schema(connect(get_settings().resolved_database_path()))
    engine = make_engine(get_settings().resolved_database_path())
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, [make_verse_input(translation="deadlinetoken verse")])

    async def _slow(**kwargs: object):
        await asyncio.sleep(6)
        yield "never"

    monkeypatch.setattr("app.services.guidance_service.stream_openai_chat", _slow)

    client = TestClient(create_app())
    with client.stream("POST", "/api/v1/guidance/stream", json={"query": "deadlinetoken"}) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())

    events = [json.loads(ln.removeprefix("data: ")) for ln in text.splitlines() if ln.startswith("data: ")]
    err = next(e for e in events if e["event"] == "error")
    assert err["data"]["code"] == "openai_deadline"
    assert err["data"].get("fallback_used") is True
    assert events[-1]["event"] == "completed"


def test_guidance_rate_limit_retrieve(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rl.db"))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("GUIDANCE_RETRIEVE_RATE_LIMIT_PER_MINUTE", "2")
    get_settings.cache_clear()

    init_schema(connect(get_settings().resolved_database_path()))

    client = TestClient(create_app())
    for _ in range(2):
        r = client.post("/api/v1/guidance/retrieve", json={"query": "anything"})
        assert r.status_code == 200
    r3 = client.post("/api/v1/guidance/retrieve", json={"query": "more"})
    assert r3.status_code == 429
    body = r3.json()
    assert body.get("error") == "rate_limit_exceeded"
    assert isinstance(body.get("detail"), dict)
    assert body["detail"].get("error") == "rate_limit_exceeded"
    assert "Retry-After" in r3.headers


def test_retrieve_cache_second_hit_skips_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    make_verse_input,
) -> None:
    db = tmp_path / "cache.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("RETRIEVE_CACHE_MAX_ENTRIES", "8")
    monkeypatch.setenv("RETRIEVE_CACHE_TTL_S", "120")
    get_settings.cache_clear()

    init_schema(connect(get_settings().resolved_database_path()))
    engine = make_engine(get_settings().resolved_database_path())
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, [make_verse_input(translation="cachetoken unique")])

    calls = {"n": 0}
    orig = RetrievalPipelineService.retrieve_with_metadata

    async def _counting(self, conn, *, query, settings):
        calls["n"] += 1
        return await orig(self, conn, query=query, settings=settings)

    monkeypatch.setattr(RetrievalPipelineService, "retrieve_with_metadata", _counting)

    client = TestClient(create_app())
    body = {"query": "cachetoken"}
    r1 = client.post("/api/v1/guidance/retrieve", json=body)
    r2 = client.post("/api/v1/guidance/retrieve", json=body)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()
    assert calls["n"] == 1
