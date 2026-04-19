"""Unit checks for the Ollama client payload shape (no network)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from app.llm.ollama_client import stream_ollama_chat


def _ndjson(lines: list[dict[str, Any]]) -> bytes:
    return ("\n".join(json.dumps(obj) for obj in lines) + "\n").encode()


async def _collect(stream: AsyncIterator[str]) -> list[str]:
    out: list[str] = []
    async for p in stream:
        out.append(p)
    return out


def _patch_transport(monkeypatch: pytest.MonkeyPatch, transport: httpx.MockTransport) -> None:
    """Wrap ``httpx.AsyncClient`` inside the ollama_client module so MockTransport is used.

    Captures the real class once and re-invokes it with the mock transport injected, avoiding
    the infinite-recursion trap that comes from replacing the module attribute with a factory
    that closes over the already-patched class.
    """
    import app.llm.ollama_client as oc

    real_cls = oc.httpx.AsyncClient

    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return real_cls(*args, **kwargs)

    monkeypatch.setattr(oc.httpx, "AsyncClient", _factory)


@pytest.mark.asyncio
async def test_stream_ollama_chat_sends_keep_alive_in_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content.decode())
        body = _ndjson(
            [
                {"message": {"content": "Hello "}, "done": False},
                {"done": True},
            ]
        )
        return httpx.Response(200, content=body, headers={"Content-Type": "application/x-ndjson"})

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    pieces = await _collect(
        stream_ollama_chat(
            base_url="http://unit-test:11434",
            model="qwen2.5:14b",
            messages=[{"role": "user", "content": "hi"}],
            keep_alive="30m",
        )
    )

    assert "".join(pieces).startswith("Hello ")
    assert captured["body"]["keep_alive"] == "30m"
    assert captured["body"]["model"] == "qwen2.5:14b"
    assert captured["body"]["stream"] is True


@pytest.mark.asyncio
async def test_stream_ollama_chat_omits_keep_alive_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        body = _ndjson(
            [
                {"message": {"content": "ok"}, "done": False},
                {"done": True},
            ]
        )
        return httpx.Response(200, content=body, headers={"Content-Type": "application/x-ndjson"})

    _patch_transport(monkeypatch, httpx.MockTransport(handler))

    await _collect(
        stream_ollama_chat(
            base_url="http://unit-test:11434",
            model="qwen2.5:14b",
            messages=[{"role": "user", "content": "hi"}],
        )
    )

    assert "keep_alive" not in captured["body"]
