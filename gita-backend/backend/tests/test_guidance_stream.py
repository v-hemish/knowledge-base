import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import connect, init_schema
from app.db.ingestion import ingest_verse_inputs
from app.db.session import make_engine, make_session_factory, session_scope
from app.llm.openai_client import OpenAIError
from app.main import create_app


@pytest.fixture
def fake_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch the OpenAI streaming client with a deterministic, validation-passing response.

    The yielded explanation contains the canonical primary citation label and the query token
    so polish + validation accept it on the first attempt.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    get_settings.cache_clear()

    async def _stream(
        *,
        base_url: str,
        model: str,
        api_key: str,
        messages: list[dict[str, str]],
        timeout: object = None,
        options: dict[str, object] | None = None,
        stream_stats: dict | None = None,
        log_request: bool = False,
        **_extra: object,
    ):
        joined = "\n".join(m.get("content") or "" for m in messages)
        assert "distincttoken" in joined
        assert "citation_key" in messages[0]["content"] or "citation_key" in joined
        assert options is not None
        if stream_stats is not None:
            stream_stats["model_request_started"] = True
            stream_stats["first_chunk_received"] = True
            stream_stats["first_chunk_latency_ms"] = 1
            stream_stats["stream_chunk_count"] = 1
            stream_stats["openai_stream_wall_ms"] = 2
        yield (
            "These verses shift attention from owning every scoreboard swing to faithful action alone. "
            "Bhagavad Gita 2.47 with distincttoken names that split clearly for obsessive metrics. "
            "Finish one bounded task before you open the dashboard again."
        )

    monkeypatch.setattr("app.services.guidance_service.stream_openai_chat", _stream)


def test_guidance_stream_contract_metadata_verses_tokens_completed(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    fake_openai: None,
    make_verse_input,
) -> None:
    db = tmp_path / "guidance.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()

    settings = get_settings()
    db_path = settings.resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, [make_verse_input()])

    client = TestClient(create_app())
    with client.stream("POST", "/api/v1/guidance/stream", json={"query": "distincttoken"}) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())

    lines = [ln for ln in text.splitlines() if ln.startswith("data: ")]
    assert len(lines) >= 4
    events = [json.loads(ln.removeprefix("data: ")) for ln in lines]
    types = [e["event"] for e in events]
    assert types[0] == "metadata"
    assert types[1] == "verses"
    assert "token" in types
    assert types[-1] == "completed"
    assert events[-1]["data"].get("generation_attempts", 0) >= 1
    lat = events[-1]["data"].get("latency_ms") or {}
    assert lat.get("retrieval_ms", -1) >= 0
    assert lat.get("through_verses_sse_ms", -1) >= lat.get("retrieval_ms", 0)
    assert lat.get("first_token_ms_from_request_start") is not None
    assert lat.get("generation_sum_ms", -1) >= 0
    assert lat.get("total_request_ms", -1) >= 0
    assert lat.get("completion_outcome") == "success"
    assert lat.get("generation_prompt_chars", 0) > 200
    assert lat.get("generation_prompt_messages") == 2
    assert lat.get("generation_estimated_input_tokens", 0) >= 1
    assert lat.get("verses_in_generation_context") == 1

    meta = events[0]["data"]
    assert meta["verse_count"] == 1
    assert meta["query"] == "distincttoken"
    assert meta.get("model") == "gpt-5-mini"
    assert meta.get("eval_debug") is False

    first_verse = events[1]["data"]["verses"][0]
    assert first_verse["citation_key"] == "2.47"
    assert first_verse["citation"] == "Bhagavad Gita 2.47"
    assert first_verse["translation"].startswith("distincttoken")


def test_guidance_stream_injects_structured_primary_label_when_model_uses_loose_ref(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    make_verse_input,
) -> None:
    """If the model emits only ``2.47`` style shorthand, service must inject
    ``Bhagavad Gita 2.47`` deterministically and avoid citation-only fallback."""
    db = tmp_path / "guidance_citation_fix.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    get_settings.cache_clear()

    db_path = get_settings().resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, [make_verse_input(translation="distincttoken verse body")])

    async def _loose_ref(**kwargs):
        stats = kwargs.get("stream_stats")
        if stats is not None:
            stats["model_request_started"] = True
            stats["first_chunk_received"] = True
            stats["first_chunk_latency_ms"] = 1
            stats["stream_chunk_count"] = 1
        yield (
            "This passage asks for focus on action itself and release from scoreboard attachment, "
            "as in 2.47. Take one clear duty and complete it without checking outcomes."
        )

    monkeypatch.setattr("app.services.guidance_service.stream_openai_chat", _loose_ref)

    client = TestClient(create_app())
    with client.stream("POST", "/api/v1/guidance/stream", json={"query": "distincttoken"}) as resp:
        text = "".join(resp.iter_text())

    events = [json.loads(ln.removeprefix("data: ")) for ln in text.splitlines() if ln.startswith("data: ")]
    token_text = "".join(e["data"].get("text", "") for e in events if e["event"] == "token")
    done = events[-1]["data"]

    assert "Bhagavad Gita 2.47" in token_text
    assert done.get("used_fallback_explanation") is False
    assert (done.get("eval") or {}).get("fallback_reason") is None


def test_guidance_stream_openai_failure_emits_error_then_completed(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    make_verse_input,
) -> None:
    """OpenAI failures must surface a structured ``error`` event, the user-readable fallback
    token, then ``completed`` (verses are already on the wire and remain valid)."""
    db = tmp_path / "guidance_fail.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    get_settings.cache_clear()

    db_path = get_settings().resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, [make_verse_input(translation="keepme distincttoken")])

    async def _boom(**kwargs):
        stats = kwargs.get("stream_stats")
        if stats is not None:
            stats["model_request_started"] = True
        raise OpenAIError("simulated openai down", code="openai_test")
        yield ""  # makes this an async generator; first __anext__ runs the raise

    monkeypatch.setattr("app.services.guidance_service.stream_openai_chat", _boom)

    client = TestClient(create_app())
    with client.stream("POST", "/api/v1/guidance/stream", json={"query": "distincttoken"}) as resp:
        text = "".join(resp.iter_text())

    events = [json.loads(ln.removeprefix("data: ")) for ln in text.splitlines() if ln.startswith("data: ")]
    types = [e["event"] for e in events]
    assert types[0] == "metadata"
    assert types[1] == "verses"
    assert "error" in types
    assert types[-1] == "completed"
    err = next(e for e in events if e["event"] == "error")
    assert err["data"]["code"] == "openai_test"
    assert err["data"]["exception_type"] == "OpenAIError"
    assert err["data"].get("fallback_used") is True
    fb = next(
        e
        for e in events
        if e["event"] == "token" and "streamed reflection is not available" in e["data"].get("text", "")
    )
    assert "authoritative" in fb["data"]["text"].lower()
    verses = next(e for e in events if e["event"] == "verses")["data"]["verses"]
    assert verses[0]["translation"] == "keepme distincttoken"
    done = events[-1]["data"]
    lat = done.get("latency_ms") or {}
    assert lat.get("completion_outcome") == "openai_error"


def test_guidance_stream_eval_debug_validation_failure_streams_deterministic_fallback(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    make_verse_input,
) -> None:
    """eval_debug must not leak invalid polished text; same safe paragraph as production."""
    db = tmp_path / "guidance_val_fail.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    get_settings.cache_clear()

    db_path = get_settings().resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, [make_verse_input(translation="keepme distincttoken")])

    async def _always_too_short(**kwargs):
        stats = kwargs.get("stream_stats")
        if stats is not None:
            stats["model_request_started"] = True
            stats["first_chunk_received"] = True
            stats["first_chunk_latency_ms"] = 1
            stats["stream_chunk_count"] = 1
        yield "Too few words. See 2.47."

    monkeypatch.setattr("app.services.guidance_service.stream_openai_chat", _always_too_short)

    client = TestClient(create_app())
    with client.stream(
        "POST",
        "/api/v1/guidance/stream",
        json={"query": "distincttoken", "eval_debug": True},
    ) as resp:
        text = "".join(resp.iter_text())

    events = [json.loads(ln.removeprefix("data: ")) for ln in text.splitlines() if ln.startswith("data: ")]
    token_text = "".join(e["data"].get("text", "") for e in events if e["event"] == "token")
    assert "clearest guidance" in token_text.lower() or "bhagavad gita 2.47" in token_text.lower()
    assert "Too few words" not in token_text
    done = events[-1]["data"]
    assert done.get("used_fallback_explanation") is True
    eval_block = done.get("eval") or {}
    assert eval_block.get("used_validation_rejected_draft") is False
    assert eval_block.get("fallback_reason") == "validation_failed"
    assert "too_short" in (eval_block.get("validation_final_reasons") or [])
    assert "Too few words" in (eval_block.get("last_polished_rejected") or "")


def test_guidance_stream_eval_debug_skips_generic_fallback_token(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    make_verse_input,
) -> None:
    db = tmp_path / "guidance_eval.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    get_settings.cache_clear()

    db_path = get_settings().resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, [make_verse_input(translation="keepme distincttoken")])

    async def _boom(**kwargs):
        if kwargs.get("stream_stats") is not None:
            kwargs["stream_stats"]["model_request_started"] = True
        raise OpenAIError("simulated down", code="openai_test")
        yield ""

    monkeypatch.setattr("app.services.guidance_service.stream_openai_chat", _boom)

    client = TestClient(create_app())
    with client.stream(
        "POST",
        "/api/v1/guidance/stream",
        json={"query": "distincttoken", "eval_debug": True},
    ) as resp:
        text = "".join(resp.iter_text())

    events = [json.loads(ln.removeprefix("data: ")) for ln in text.splitlines() if ln.startswith("data: ")]
    types = [e["event"] for e in events]
    assert types[0] == "metadata"
    assert types[1] == "verses"
    assert "error" in types
    assert types[-1] == "completed"
    err = next(e for e in events if e["event"] == "error")
    assert err["data"]["code"] == "openai_test"
    assert err["data"].get("fallback_used") is False
    assert not any(
        e["event"] == "token" and "streamed reflection is not available" in e["data"].get("text", "").lower()
        for e in events
    )
    done = events[-1]["data"]
    assert "eval" in done
    assert done["eval"].get("fallback_reason") == "openai_test"
    assert "simulated down" in (done["eval"].get("raw_error") or "")


def test_guidance_stream_passes_openai_key_and_options(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    make_verse_input,
) -> None:
    """Sanity-check the wiring: api_key, model, and decoding options reach the client."""
    db = tmp_path / "guidance_openai.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    get_settings.cache_clear()

    db_path = get_settings().resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, [make_verse_input()])

    captured: dict[str, object] = {}

    async def _fake_openai_stream(
        *,
        base_url: str,
        model: str,
        api_key: str,
        messages: list[dict[str, str]],
        timeout: object = None,
        options: dict[str, object] | None = None,
        stream_stats: dict | None = None,
        log_request: bool = False,
        **_extra: object,
    ):
        captured["model"] = model
        captured["api_key"] = api_key
        captured["options"] = options
        if stream_stats is not None:
            stream_stats["model_request_started"] = True
            stream_stats["first_chunk_received"] = True
            stream_stats["first_chunk_latency_ms"] = 1
            stream_stats["stream_chunk_count"] = 1
            stream_stats["openai_stream_wall_ms"] = 2
        yield (
            "These verses shift attention from owning every scoreboard swing to faithful action alone. "
            "Bhagavad Gita 2.47 with distincttoken names that split clearly for obsessive metrics. "
            "Finish one bounded task before you open the dashboard again."
        )

    monkeypatch.setattr("app.services.guidance_service.stream_openai_chat", _fake_openai_stream)

    client = TestClient(create_app())
    with client.stream("POST", "/api/v1/guidance/stream", json={"query": "distincttoken"}) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())

    events = [
        json.loads(ln.removeprefix("data: "))
        for ln in text.splitlines()
        if ln.startswith("data: ")
    ]
    types = [e["event"] for e in events]
    assert types[0] == "metadata"
    assert types[-1] == "completed"
    assert "token" in types

    meta = events[0]["data"]
    assert meta["model"] == "gpt-5-mini"

    done = events[-1]["data"]
    lat = done.get("latency_ms") or {}
    assert lat.get("completion_outcome") == "success"

    assert captured["model"] == "gpt-5-mini"
    assert captured["api_key"] == "sk-test"
    opts = captured["options"] or {}
    assert "num_predict" in opts
    assert "temperature" in opts


def test_guidance_stream_puts_two_verses_in_generation_context_when_available(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    fake_openai: None,
    make_verse_input,
) -> None:
    db = tmp_path / "guidance_two.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("GUIDANCE_GENERATION_MAX_VERSES", "2")
    get_settings.cache_clear()

    settings = get_settings()
    db_path = settings.resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(
            session,
            [
                make_verse_input(translation="distincttoken action fruits verse one"),
                make_verse_input(
                    chapter=6,
                    verse=5,
                    citation_key="6.5",
                    translation="distincttoken lift the mind steady yoga",
                ),
            ],
        )

    client = TestClient(create_app())
    with client.stream("POST", "/api/v1/guidance/stream", json={"query": "distincttoken"}) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())

    events = [
        json.loads(ln.removeprefix("data: "))
        for ln in text.splitlines()
        if ln.startswith("data: ")
    ]
    lat = events[-1]["data"].get("latency_ms") or {}
    assert lat.get("verses_in_generation_context") == 2
    assert lat.get("generation_max_verses_budget") == 2


def test_guidance_stream_two_verse_ask_overrides_burnout_one_verse_budget(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    fake_openai: None,
    make_verse_input,
) -> None:
    """Explicit 'two verses' should still pass two cards into the model when the DB has two hits."""
    db = tmp_path / "guidance_two_burnout.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("GUIDANCE_BURNOUT_GENERATION_MAX_VERSES", "1")
    monkeypatch.setenv("GUIDANCE_GENERATION_MAX_VERSES", "1")
    get_settings.cache_clear()

    settings = get_settings()
    db_path = settings.resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(
            session,
            [
                make_verse_input(translation="distincttoken burnout metrics fruits"),
                make_verse_input(
                    chapter=6,
                    verse=5,
                    citation_key="6.5",
                    translation="distincttoken steady mind lift",
                ),
            ],
        )

    q = (
        "I obsess over work results and burn out; distincttoken; "
        "please give me two verses to reflect on"
    )
    client = TestClient(create_app())
    with client.stream("POST", "/api/v1/guidance/stream", json={"query": q}) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())

    events = [
        json.loads(ln.removeprefix("data: "))
        for ln in text.splitlines()
        if ln.startswith("data: ")
    ]
    lat = events[-1]["data"].get("latency_ms") or {}
    assert lat.get("verses_in_generation_context") == 2
    assert lat.get("generation_max_verses_budget") == 2


def test_guidance_stream_options_preflight_cors() -> None:
    """Browser cross-origin POST sends OPTIONS first; CORS middleware must answer 200."""
    client = TestClient(create_app())
    r = client.options(
        "/api/v1/guidance/stream",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,accept",
        },
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"
