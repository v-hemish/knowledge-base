"""HTTP streaming client for the OpenAI Chat Completions API.

Sole generation backend for :mod:`app.services.guidance_service`. Keeps the explanation-only
contract: this client never returns verse text and is only invoked after canonical verses
have already been streamed to the client.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import Settings

_log = logging.getLogger(__name__)


class OpenAIError(Exception):
    """Raised when OpenAI cannot stream a completion (verses may already have been sent)."""

    def __init__(self, message: str, *, code: str = "openai_unavailable") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def openai_stream_timeout(settings: Settings) -> httpx.Timeout:
    """Timeouts for long-lived OpenAI streams (connect vs read/write separated)."""
    return httpx.Timeout(
        connect=settings.openai_connect_timeout_s,
        read=settings.openai_read_timeout_s,
        write=settings.openai_write_timeout_s,
        pool=10.0,
    )


def _summarize_messages_for_log(messages: list[dict[str, str]], *, max_chars: int = 600) -> dict[str, Any]:
    parts: list[dict[str, Any]] = []
    for m in messages:
        c = m.get("content") or ""
        parts.append({"role": m.get("role"), "chars": len(c), "head": c[:120].replace("\n", " ")})
    total = sum(p["chars"] for p in parts)
    joined = "\n".join((m.get("content") or "") for m in messages)
    return {"message_count": len(messages), "total_chars": total, "preview": joined[:max_chars]}


# OpenAI reasoning-family models (gpt-5, o1, o3, o4 lines) reject custom ``temperature`` and
# ``top_p`` values with HTTP 400 ("Only the default (1) value is supported"). Detect by name
# prefix and drop those fields from the payload so the same per-attempt option dict produced
# by ``guidance_service`` works across both reasoning and classic chat models. The detection is
# intentionally conservative — only well-known prefixes — so unfamiliar model names default to
# the safe "send everything" path used by gpt-4o-mini, gpt-3.5-turbo, etc.
_REASONING_MODEL_PREFIXES: tuple[str, ...] = ("gpt-5", "o1", "o3", "o4")


def _model_supports_custom_sampling(model: str) -> bool:
    m = (model or "").strip().lower()
    return not m.startswith(_REASONING_MODEL_PREFIXES)


def _build_payload(
    *,
    model: str,
    messages: list[dict[str, str]],
    options: dict[str, object] | None,
) -> dict[str, object]:
    """Translate the generic decoding options dict into OpenAI Chat Completions fields.

    Mapping:
        - ``temperature``      -> ``temperature`` (dropped for reasoning-family models)
        - ``top_p``            -> ``top_p`` (dropped for reasoning-family models)
        - ``num_predict``      -> ``max_completion_tokens`` (GPT-5 family field; the older
          ``max_tokens`` is rejected by these models, so we always emit the new key)
        - ``reasoning_effort`` -> only emitted for reasoning-family models. Reasoning models
          consume ``max_completion_tokens`` for *internal* reasoning before any visible content
          token is emitted; with a small prompt budget, ``effort="minimal"`` is required to
          guarantee any user-visible output for short guidance answers (otherwise the stream
          terminates with ``finish_reason="length"`` and zero content chunks).
        - ``repeat_penalty``   -> dropped (no OpenAI equivalent; logged once at DEBUG).
    """
    payload: dict[str, object] = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    if not options:
        return payload

    sampling_ok = _model_supports_custom_sampling(model)
    if not sampling_ok:
        # ``minimal`` is the lowest-overhead reasoning level on gpt-5/o-series models. For our
        # 2-4 sentence guidance answers we never want extended reasoning to eat the entire
        # token budget. Callers can override by passing ``reasoning_effort`` explicitly in
        # ``options``.
        payload["reasoning_effort"] = options.get("reasoning_effort", "minimal")

    if "temperature" in options:
        if sampling_ok:
            payload["temperature"] = float(options["temperature"])  # type: ignore[arg-type]
        else:
            _log.debug(
                "openai_client_drops_temperature_for_reasoning_model",
                extra={"model": model, "value": options["temperature"]},
            )
    if "top_p" in options:
        if sampling_ok:
            payload["top_p"] = float(options["top_p"])  # type: ignore[arg-type]
        else:
            _log.debug(
                "openai_client_drops_top_p_for_reasoning_model",
                extra={"model": model, "value": options["top_p"]},
            )
    if "num_predict" in options:
        payload["max_completion_tokens"] = int(options["num_predict"])  # type: ignore[arg-type]
    if "repeat_penalty" in options:
        # OpenAI Chat Completions has no direct equivalent; ``frequency_penalty`` is similar in
        # spirit but not a 1:1 swap. Dropping is safer than guessing a translation that could
        # silently change generation quality during benchmarking.
        _log.debug(
            "openai_client_drops_repeat_penalty",
            extra={"value": options["repeat_penalty"]},
        )
    return payload


async def stream_openai_chat(
    *,
    base_url: str,
    model: str,
    api_key: str,
    messages: list[dict[str, str]],
    timeout: httpx.Timeout | None = None,
    options: dict[str, object] | None = None,
    stream_stats: dict[str, Any] | None = None,
    log_request: bool = False,
) -> AsyncIterator[str]:
    """Stream assistant string tokens from the OpenAI Chat Completions endpoint.

    On transport, auth, or HTTP failures, raises :class:`OpenAIError` so callers can emit a
    structured SSE error while keeping the verse cards intact.

    ``stream_stats`` (optional) is mutated with timing/chunk counts using ``openai_*`` keys so
    eval JSON files are unambiguous about which backend produced the numbers.
    """
    if not api_key:
        raise OpenAIError(
            "OPENAI_API_KEY is not set. Configure it in backend/.env (kept out of git) or "
            "export it before starting the API. Verses already sent remain valid.",
            code="openai_auth_missing",
        )

    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = _build_payload(model=model, messages=messages, options=options)
    client_timeout = timeout or httpx.Timeout(120.0)

    if stream_stats is not None:
        stream_stats.setdefault("openai_url", url)
        stream_stats.setdefault("openai_model", model)

    if log_request:
        _log.info(
            "openai_chat_request",
            extra={
                "openai_url": url,
                "openai_model": model,
                "options": options,
                "messages_summary": _summarize_messages_for_log(messages),
            },
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    t_req = time.perf_counter()
    content_chunks = 0

    try:
        async with httpx.AsyncClient(timeout=client_timeout) as client:
            try:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    if stream_stats is not None:
                        stream_stats["model_request_started"] = True
                        stream_stats["openai_http_status"] = resp.status_code

                    if resp.status_code >= 400:
                        raw_body = await resp.aread()
                        snippet = raw_body[:1200].decode("utf-8", errors="replace")
                        if stream_stats is not None:
                            stream_stats["openai_response_body_snippet"] = snippet
                        if resp.status_code in (401, 403):
                            raise OpenAIError(
                                "OpenAI rejected the API key (HTTP "
                                f"{resp.status_code}). Verify OPENAI_API_KEY and project access. "
                                f"Body: {snippet[:400]}",
                                code="openai_auth_error",
                            )
                        if resp.status_code == 404:
                            raise OpenAIError(
                                f"OpenAI returned 404 for model '{model}'. Confirm the model "
                                f"name (e.g. gpt-5-mini, gpt-4o-mini). Body: {snippet[:400]}",
                                code="openai_model_not_found",
                            )
                        if resp.status_code == 429:
                            raise OpenAIError(
                                "OpenAI rate-limited or quota-exceeded (HTTP 429). Retry later "
                                f"or check billing. Body: {snippet[:400]}",
                                code="openai_rate_limited",
                            )
                        raise OpenAIError(
                            "OpenAI returned an HTTP error while starting generation "
                            f"(HTTP {resp.status_code}). Body: {snippet[:500]}",
                            code="openai_http_error",
                        )

                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if not line.startswith("data:"):
                            # OpenAI SSE may include comment lines (``: keep-alive``) we skip.
                            continue
                        data = line[len("data:"):].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            _log.warning("openai_non_json_line", extra={"line": data[:200]})
                            continue

                        if isinstance(chunk, dict) and chunk.get("error"):
                            err = chunk["error"]
                            err_msg = err.get("message") if isinstance(err, dict) else str(err)
                            if stream_stats is not None:
                                stream_stats["openai_stream_error_line"] = (err_msg or "")[:800]
                            raise OpenAIError(
                                f"OpenAI reported an error mid-stream: {err_msg}",
                                code="openai_api_error",
                            )

                        choices = chunk.get("choices") or []
                        if not choices:
                            continue
                        delta = (choices[0] or {}).get("delta") or {}
                        piece = delta.get("content") or ""
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
                        stream_stats["openai_stream_wall_ms"] = int((time.perf_counter() - t_req) * 1000)

                    if content_chunks == 0:
                        raise OpenAIError(
                            "OpenAI returned no assistant content in the stream (0 chunks). "
                            "The model name may be invalid or the response was empty.",
                            code="openai_empty_stream",
                        )

                    if log_request:
                        _log.info(
                            "openai_chat_stream_done",
                            extra={
                                "openai_model": model,
                                "stream_chunk_count": content_chunks,
                                "elapsed_ms": int((time.perf_counter() - t_req) * 1000),
                            },
                        )

            except httpx.ConnectError as exc:
                raise OpenAIError(
                    "Could not connect to the OpenAI API. Check OPENAI_BASE_URL and network.",
                    code="openai_connect_error",
                ) from exc
            except (httpx.ReadTimeout, httpx.WriteTimeout) as exc:
                raise OpenAIError(
                    "OpenAI stopped responding while streaming. Retrieved verses remain valid.",
                    code="openai_timeout",
                ) from exc
            except (httpx.ConnectTimeout, httpx.PoolTimeout) as exc:
                raise OpenAIError(
                    "OpenAI connection timed out. Retrieved verses remain valid.",
                    code="openai_timeout",
                ) from exc
    except OpenAIError:
        raise
    except httpx.HTTPError as exc:
        raise OpenAIError(
            f"OpenAI request failed: {type(exc).__name__}: {exc}. Retrieved verses remain valid.",
            code="openai_http_error",
        ) from exc
