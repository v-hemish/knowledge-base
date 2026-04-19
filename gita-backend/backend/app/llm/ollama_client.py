"""HTTP streaming client for a local Ollama server."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import Settings

_log = logging.getLogger(__name__)

# Wall time since the previous successful Ollama chat stream ended (same process). Used to
# correlate long first-token latency with idle / cold-runner behavior in logs and ``stream_stats``.
_last_successful_stream_end_monotonic: float | None = None


class OllamaError(Exception):
    """Raised when Ollama cannot stream a completion (verses may already have been sent to the client)."""

    def __init__(self, message: str, *, code: str = "ollama_unavailable") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def ollama_stream_timeout(settings: Settings) -> httpx.Timeout:
    """Timeouts for long-lived chat streams (connect vs read/write separated)."""
    return httpx.Timeout(
        connect=settings.ollama_connect_timeout_s,
        read=settings.ollama_read_timeout_s,
        write=settings.ollama_write_timeout_s,
        pool=10.0,
    )


def _summarize_messages_for_log(messages: list[dict[str, str]], *, max_chars: int = 600) -> dict[str, Any]:
    """Compact, log-safe view of chat messages (never log full verse blocks at INFO)."""
    parts: list[dict[str, Any]] = []
    for m in messages:
        c = m.get("content") or ""
        parts.append({"role": m.get("role"), "chars": len(c), "head": c[:120].replace("\n", " ")})
    total = sum(p["chars"] for p in parts)
    joined = "\n".join((m.get("content") or "") for m in messages)
    return {"message_count": len(messages), "total_chars": total, "preview": joined[:max_chars]}


async def stream_ollama_chat(
    *,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: httpx.Timeout | None = None,
    options: dict[str, object] | None = None,
    stream_stats: dict[str, Any] | None = None,
    log_request: bool = False,
    keep_alive: str | None = None,
) -> AsyncIterator[str]:
    """
    Stream assistant string tokens from a local Ollama server.

    On transport or HTTP failures, raises ``OllamaError`` so callers can emit a structured SSE
    error while keeping verse cards intact.

    ``stream_stats`` (optional) is mutated with timing/chunk counts for diagnostics.

    FUTURE: cancellation, retries, and prompt caching keyed by verse revision.
    """
    global _last_successful_stream_end_monotonic

    url = f"{base_url.rstrip('/')}/api/chat"
    payload: dict[str, object] = {"model": model, "messages": messages, "stream": True}
    if options:
        payload["options"] = options
    if keep_alive:
        payload["keep_alive"] = keep_alive
    client_timeout = timeout or httpx.Timeout(120.0)

    if stream_stats is not None:
        stream_stats.setdefault("ollama_url", url)
        stream_stats.setdefault("ollama_model", model)

    if log_request:
        _log.info(
            "ollama_chat_request",
            extra={
                "ollama_url": url,
                "ollama_model": model,
                "options": options,
                "messages_summary": _summarize_messages_for_log(messages),
            },
        )

    t_req = time.perf_counter()
    content_chunks = 0
    if stream_stats is not None and _last_successful_stream_end_monotonic is not None:
        stream_stats["ollama_seconds_since_previous_stream_end"] = round(
            time.monotonic() - _last_successful_stream_end_monotonic,
            3,
        )

    try:
        async with httpx.AsyncClient(timeout=client_timeout) as client:
            try:
                async with client.stream("POST", url, json=payload) as resp:
                    if stream_stats is not None:
                        stream_stats["model_request_started"] = True
                        stream_stats["ollama_http_status"] = resp.status_code

                    if resp.status_code >= 400:
                        raw_body = await resp.aread()
                        snippet = raw_body[:1200].decode("utf-8", errors="replace")
                        if stream_stats is not None:
                            stream_stats["ollama_response_body_snippet"] = snippet
                        hint = ""
                        if resp.status_code == 404:
                            hint = " Often means the model is not installed (`ollama pull <model>`)."
                        raise OllamaError(
                            "Ollama returned an HTTP error while starting generation "
                            f"(HTTP {resp.status_code}). Body: {snippet[:500]}{hint}",
                            code="ollama_http_error",
                        )

                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            _log.warning("ollama_non_json_line", extra={"line": line[:200]})
                            continue

                        if isinstance(chunk, dict) and chunk.get("error"):
                            err_msg = str(chunk["error"])
                            if stream_stats is not None:
                                stream_stats["ollama_stream_error_line"] = err_msg[:800]
                            raise OllamaError(
                                f"Ollama reported an error in the stream: {err_msg}",
                                code="ollama_api_error",
                            )

                        if chunk.get("done"):
                            break
                        msg = chunk.get("message") or {}
                        piece = msg.get("content") or ""
                        if piece:
                            content_chunks += 1
                            if stream_stats is not None:
                                if not stream_stats.get("first_chunk_received"):
                                    stream_stats["first_chunk_received"] = True
                                    stream_stats["first_chunk_latency_ms"] = int(
                                        (time.perf_counter() - t_req) * 1000
                                    )
                                stream_stats["stream_chunk_count"] = content_chunks
                            yield str(piece)

                    if stream_stats is not None:
                        stream_stats["ollama_stream_wall_ms"] = int((time.perf_counter() - t_req) * 1000)

                    if content_chunks == 0:
                        raise OllamaError(
                            "Ollama returned no assistant content in the stream (0 chunks). "
                            "The model name may be invalid, the runner may be out of memory, "
                            "or the server closed the stream immediately.",
                            code="ollama_empty_stream",
                        )

                    _last_successful_stream_end_monotonic = time.monotonic()

                    if log_request:
                        _log.info(
                            "ollama_chat_stream_done",
                            extra={
                                "ollama_model": model,
                                "stream_chunk_count": content_chunks,
                                "elapsed_ms": int((time.perf_counter() - t_req) * 1000),
                            },
                        )

            except httpx.ConnectError as exc:
                raise OllamaError(
                    "Could not connect to the local Ollama server. "
                    "Start Ollama or check OLLAMA_BASE_URL. Retrieved verses remain valid.",
                    code="ollama_connect_error",
                ) from exc
            except (httpx.ReadTimeout, httpx.WriteTimeout) as exc:
                raise OllamaError(
                    "Ollama stopped responding while streaming. Retrieved verses remain valid.",
                    code="ollama_timeout",
                ) from exc
            except (httpx.ConnectTimeout, httpx.PoolTimeout) as exc:
                raise OllamaError(
                    "Ollama connection timed out. Retrieved verses remain valid.",
                    code="ollama_timeout",
                ) from exc
    except OllamaError:
        raise
    except httpx.HTTPError as exc:
        raise OllamaError(
            f"Ollama request failed: {type(exc).__name__}: {exc}. Retrieved verses remain valid.",
            code="ollama_http_error",
        ) from exc
