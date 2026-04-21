"""Unit checks for the OpenAI Chat Completions streaming client (no network)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from app.llm.openai_client import OpenAIError, stream_openai_chat


def _sse(events: list[dict[str, Any] | str]) -> bytes:
    """Build an SSE byte body from chunk dicts (delta payloads) and/or raw control strings.

    A dict ``d`` becomes ``data: {json}\\n\\n``; the literal string ``"[DONE]"`` becomes
    ``data: [DONE]\\n\\n``; any other string is emitted verbatim plus ``\\n\\n``.
    """
    parts: list[str] = []
    for ev in events:
        if isinstance(ev, dict):
            parts.append(f"data: {json.dumps(ev)}\n\n")
        elif ev == "[DONE]":
            parts.append("data: [DONE]\n\n")
        else:
            parts.append(f"{ev}\n\n")
    return "".join(parts).encode()


def _delta(content: str) -> dict[str, Any]:
    return {"choices": [{"delta": {"content": content}, "index": 0, "finish_reason": None}]}


async def _collect(stream: AsyncIterator[str]) -> list[str]:
    out: list[str] = []
    async for p in stream:
        out.append(p)
    return out


def _patch_transport(monkeypatch: pytest.MonkeyPatch, transport: httpx.MockTransport) -> None:
    """Wrap ``httpx.AsyncClient`` inside ``openai_client`` so MockTransport is used.

    Mirrors the prior local-backend test pattern (avoids the
    ``RecursionError`` trap from naive monkeypatching).
    """
    import app.llm.openai_client as oc

    real_cls = oc.httpx.AsyncClient

    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return real_cls(*args, **kwargs)

    monkeypatch.setattr(oc.httpx, "AsyncClient", _factory)


@pytest.mark.asyncio
async def test_stream_openai_chat_drops_sampling_for_reasoning_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """gpt-5-mini (and the o1/o3/o4 lines) reject any non-default ``temperature`` or ``top_p``
    with HTTP 400. The client must strip both fields so the same per-attempt option dict that
    works for gpt-4o-mini also works here without the caller knowing about model families."""
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content.decode())
        body = _sse([_delta("Hello "), _delta("world."), "[DONE]"])
        return httpx.Response(
            200, content=body, headers={"Content-Type": "text/event-stream"}
        )

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    pieces = await _collect(
        stream_openai_chat(
            base_url="https://api.openai.com/v1",
            model="gpt-5-mini",
            api_key="sk-test",
            messages=[{"role": "user", "content": "hi"}],
            options={
                "temperature": 0.2,
                "top_p": 0.9,
                "num_predict": 220,
                "repeat_penalty": 1.15,
            },
        )
    )

    assert "".join(pieces) == "Hello world."
    assert captured["url"].endswith("/chat/completions")
    body = captured["body"]
    assert body["model"] == "gpt-5-mini"
    assert body["stream"] is True
    # GPT-5 family field name; the legacy ``max_tokens`` would be rejected.
    assert body["max_completion_tokens"] == 220
    # Sampling fields MUST be absent for reasoning-family models — sending them produces the
    # exact HTTP 400 we hit during the first gpt-5-mini bench (``Only the default (1) value
    # is supported``).
    assert "temperature" not in body
    assert "top_p" not in body
    assert "repeat_penalty" not in body
    assert captured["headers"].get("authorization") == "Bearer sk-test"


@pytest.mark.asyncio
async def test_stream_openai_chat_emits_reasoning_effort_minimal_for_reasoning_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reasoning models consume ``max_completion_tokens`` on internal reasoning before any
    visible token. ``reasoning_effort=minimal`` keeps that overhead small enough for short
    guidance answers; without it, gpt-5-mini routinely returns zero content chunks and
    ``finish_reason=length`` with our typical 1.5k-input prompt + 1024 completion budget."""
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(200, content=_sse([_delta("hi"), "[DONE]"]))

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    await _collect(
        stream_openai_chat(
            base_url="https://api.openai.com/v1",
            model="gpt-5-mini",
            api_key="sk-test",
            messages=[{"role": "user", "content": "hi"}],
            options={"num_predict": 1024},
        )
    )

    assert captured["body"]["reasoning_effort"] == "minimal"
    # reasoning_effort must NOT leak into classic-model payloads — covered by the next test.


@pytest.mark.asyncio
async def test_stream_openai_chat_omits_reasoning_effort_for_classic_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(200, content=_sse([_delta("hi"), "[DONE]"]))

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    await _collect(
        stream_openai_chat(
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            api_key="sk-test",
            messages=[{"role": "user", "content": "hi"}],
            options={"temperature": 0.2, "num_predict": 220},
        )
    )

    assert "reasoning_effort" not in captured["body"]


@pytest.mark.asyncio
async def test_stream_openai_chat_keeps_sampling_for_gpt4o_mini(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Classic chat models (gpt-4o-mini, gpt-3.5-turbo, etc.) DO accept custom sampling and
    must continue to receive ``temperature`` and ``top_p`` so the reasoning-model strip does
    not silently degrade decoding for those backends."""
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        body = _sse([_delta("ok"), "[DONE]"])
        return httpx.Response(
            200, content=body, headers={"Content-Type": "text/event-stream"}
        )

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    await _collect(
        stream_openai_chat(
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            api_key="sk-test",
            messages=[{"role": "user", "content": "hi"}],
            options={"temperature": 0.2, "top_p": 0.9, "num_predict": 220},
        )
    )

    body = captured["body"]
    assert body["temperature"] == 0.2
    assert body["top_p"] == 0.9
    assert body["max_completion_tokens"] == 220


@pytest.mark.asyncio
async def test_stream_openai_chat_records_stream_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        body = _sse([_delta("Hi"), "[DONE]"])
        return httpx.Response(
            200, content=body, headers={"Content-Type": "text/event-stream"}
        )

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    stats: dict[str, Any] = {}
    await _collect(
        stream_openai_chat(
            base_url="https://api.openai.com/v1",
            model="gpt-5-mini",
            api_key="sk-test",
            messages=[{"role": "user", "content": "hi"}],
            stream_stats=stats,
        )
    )

    assert stats["openai_url"].endswith("/chat/completions")
    assert stats["openai_model"] == "gpt-5-mini"
    assert stats["openai_http_status"] == 200
    assert stats["model_request_started"] is True
    assert stats["first_chunk_received"] is True
    assert stats["stream_chunk_count"] == 1
    assert isinstance(stats["first_chunk_latency_ms"], int)
    assert isinstance(stats["openai_stream_wall_ms"], int)


@pytest.mark.asyncio
async def test_stream_openai_chat_missing_key_raises_auth_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Even with a working transport, an empty key must short-circuit before the network call.
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_sse([_delta("nope"), "[DONE]"]))

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    with pytest.raises(OpenAIError) as exc_info:
        await _collect(
            stream_openai_chat(
                base_url="https://api.openai.com/v1",
                model="gpt-5-mini",
                api_key="",
                messages=[{"role": "user", "content": "hi"}],
            )
        )
    assert exc_info.value.code == "openai_auth_missing"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expected_code"),
    [
        (401, "openai_auth_error"),
        (403, "openai_auth_error"),
        (404, "openai_model_not_found"),
        (429, "openai_rate_limited"),
        (500, "openai_http_error"),
    ],
)
async def test_stream_openai_chat_maps_http_errors_to_codes(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    expected_code: str,
) -> None:
    # Parametrized (rather than looped) so each case gets a fresh monkeypatch and the
    # ``_patch_transport`` capture-and-wrap pattern does not chain into the previous
    # iteration's MockTransport (which would hide later 4xx codes behind earlier ones).
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status,
            content=json.dumps({"error": {"message": "nope"}}).encode(),
            headers={"Content-Type": "application/json"},
        )

    _patch_transport(monkeypatch, httpx.MockTransport(handler))
    with pytest.raises(OpenAIError) as exc_info:
        await _collect(
            stream_openai_chat(
                base_url="https://api.openai.com/v1",
                model="gpt-5-mini",
                api_key="sk-test",
                messages=[{"role": "user", "content": "hi"}],
            )
        )
    assert exc_info.value.code == expected_code


@pytest.mark.asyncio
async def test_stream_openai_chat_empty_stream_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        # Only a [DONE] sentinel, no content delta — must raise empty_stream so the caller can
        # fall back instead of streaming an empty explanation.
        return httpx.Response(200, content=_sse(["[DONE]"]))

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    with pytest.raises(OpenAIError) as exc_info:
        await _collect(
            stream_openai_chat(
                base_url="https://api.openai.com/v1",
                model="gpt-5-mini",
                api_key="sk-test",
                messages=[{"role": "user", "content": "hi"}],
            )
        )
    assert exc_info.value.code == "openai_empty_stream"


@pytest.mark.asyncio
async def test_stream_openai_chat_mid_stream_error_raises_api_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        # First a normal delta, then an error envelope mid-stream — the client must raise so
        # the partial draft never reaches the polish/validate pipeline as a complete answer.
        body = _sse(
            [
                _delta("Partial "),
                {"error": {"message": "context_length_exceeded"}},
                "[DONE]",
            ]
        )
        return httpx.Response(
            200, content=body, headers={"Content-Type": "text/event-stream"}
        )

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    with pytest.raises(OpenAIError) as exc_info:
        await _collect(
            stream_openai_chat(
                base_url="https://api.openai.com/v1",
                model="gpt-5-mini",
                api_key="sk-test",
                messages=[{"role": "user", "content": "hi"}],
            )
        )
    assert exc_info.value.code == "openai_api_error"
    assert "context_length_exceeded" in exc_info.value.message


@pytest.mark.asyncio
async def test_stream_openai_chat_skips_comment_and_blank_lines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        # Some OpenAI proxies emit ``: keep-alive`` comment lines; the client must ignore them.
        chunks = [
            ": keep-alive",
            _delta("Hi"),
            "",
            "[DONE]",
        ]
        return httpx.Response(200, content=_sse(chunks))

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    pieces = await _collect(
        stream_openai_chat(
            base_url="https://api.openai.com/v1",
            model="gpt-5-mini",
            api_key="sk-test",
            messages=[{"role": "user", "content": "hi"}],
        )
    )
    assert "".join(pieces) == "Hi"
