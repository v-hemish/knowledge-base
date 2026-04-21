from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import sqlite3
import threading
import time
import traceback
from collections.abc import AsyncIterator, Iterator
from typing import Any

from app.core.config import Settings
from app.llm.guidance_validation import (
    build_regeneration_instruction,
    deterministic_fallback_explanation,
    trim_explanation_to_limits,
    validate_guidance_explanation,
)
from app.llm.openai_client import OpenAIError, openai_stream_timeout, stream_openai_chat
from app.llm.prompts import build_guidance_messages, build_no_verses_general_messages
from app.llm.query_intent import (
    analyze_query,
    rank_verses_by_intent_and_fit,
    select_verses_for_generation,
    wants_two_verse_generation,
)
from app.llm.theme_routing import apply_theme_ordered_pins
from app.llm.stream_buffer import (
    enforce_primary_citation_label,
    normalize_primary_citation_label,
    polish_guidance_full_text,
    salvage_missing_primary_citation,
)
from app.models.verse import Verse
from app.retrieval.pipeline import retrieve_verses_for_query
from app.schemas.guidance import GuidanceRequest, GuidanceStreamEvent, VerseCard

_log = logging.getLogger(__name__)

_FALLBACK_TOKEN_TEXT = (
    "A streamed reflection is not available right now. The verses above are the "
    "authoritative text—read them in context. You can retry later."
)

_PROD_METRICS_LOCK = threading.Lock()
_PROD_METRICS: dict[str, int] = {
    "requests_total": 0,
    "fallback_total": 0,
    "validation_failures_total": 0,
    "user_visible_errors_total": 0,
}


def _record_prod_metrics(
    *,
    used_fallback: bool,
    validation_failures: int,
    user_visible_error: bool,
) -> dict[str, int]:
    with _PROD_METRICS_LOCK:
        _PROD_METRICS["requests_total"] += 1
        if used_fallback:
            _PROD_METRICS["fallback_total"] += 1
        _PROD_METRICS["validation_failures_total"] += max(0, validation_failures)
        if user_visible_error:
            _PROD_METRICS["user_visible_errors_total"] += 1
        return dict(_PROD_METRICS)


def _select_generation_model(settings: Settings, *, query: str) -> tuple[str, int]:
    pct = max(0, min(100, settings.guidance_primary_model_rollout_percent))
    bucket = int(hashlib.sha256(query.encode("utf-8")).hexdigest()[:8], 16) % 100
    if pct >= 100 or bucket < pct:
        return settings.openai_model, bucket
    fallback = (settings.openai_fallback_model or "").strip()
    return (fallback or settings.openai_model), bucket


def _render_primary_citation_deterministically(text: str, *, primary_citation_key: str) -> str:
    """Render the canonical primary citation label deterministically.

    This path is intentionally model-agnostic: OpenAI may emit loose refs like ``2.47`` or
    malformed fragments; we always normalize and enforce the exact structured label from
    retrieval metadata before validation.
    """
    out = normalize_primary_citation_label(text, primary_citation_key=primary_citation_key)
    out = salvage_missing_primary_citation(out, primary_citation_key=primary_citation_key)
    out = enforce_primary_citation_label(out, primary_citation_key=primary_citation_key)
    label = f"Bhagavad Gita {primary_citation_key}"
    if not re.search(rf"\b{re.escape(label)}\b", out):
        # Absolute guarantee for strict OpenAI path: never depend on model-written citation prose.
        out = out.rstrip()
        out = f"{out} ({label})." if out else f"{label}."
    return out


def _verse_cards(verses: list[Verse]) -> list[VerseCard]:
    return [
        VerseCard(
            chapter=v.chapter,
            verse=v.verse,
            citation_key=v.citation_key,
            citation=v.citation,
            translation=v.translation,
            sanskrit=v.sanskrit,
            transliteration=v.transliteration,
            theme_tags=v.theme_tags,
            situation_tags=v.situation_tags,
            use_with_care_tags=v.use_with_care_tags,
            translation_source=v.translation_source,
        )
        for v in verses
    ]


def _fallback_events(
    exc: OpenAIError, *, eval_debug: bool
) -> Iterator[GuidanceStreamEvent]:
    """Structured error for clients plus a user-readable token (verses already sent)."""
    yield GuidanceStreamEvent(
        event="error",
        data={
            "code": exc.code,
            "message": exc.message,
            "fallback_used": not eval_debug,
            "exception_type": type(exc).__name__,
            "detail": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc() if eval_debug else None,
        },
    )
    if not eval_debug:
        yield GuidanceStreamEvent(event="token", data={"text": _FALLBACK_TOKEN_TEXT})


def _empty_eval_debug() -> dict[str, Any]:
    return {
        "eval_debug": False,
        "model_request_started": False,
        "first_chunk_received": False,
        "first_chunk_latency_ms": None,
        "stream_chunk_count": 0,
        "raw_error": None,
        "fallback_reason": None,
        "openai_http_status": None,
        "openai_response_body_snippet": None,
        "openai_stream_error_line": None,
        "validation_final_reasons": None,
        "last_polished_rejected": None,
        "used_validation_rejected_draft": False,
    }


def _generation_prompt_telemetry(messages: list[dict[str, str]]) -> dict[str, int]:
    """Rough input size (chars + ~token estimate) without calling the tokenizer."""
    total_chars = sum(len(m.get("content") or "") for m in messages)
    return {
        "generation_prompt_chars": total_chars,
        "generation_prompt_messages": len(messages),
        "generation_estimated_input_tokens": max(1, total_chars // 4),
    }


def _iter_explanation_sse_chunks(text: str) -> Iterator[str]:
    """Minimal SSE chunking: one event for all short answers; larger groups when longer."""
    t = (text or "").strip()
    if not t:
        return
    wc = len(t.split())
    if wc <= 100:
        yield t + " "
        return
    parts = re.split(r"(?<=[.!?])\s+", t)
    buf = ""
    for p in parts:
        s = p.strip()
        if not s:
            continue
        if not buf:
            buf = s
            continue
        if len((buf + " " + s).split()) <= 55:
            buf = f"{buf} {s}"
        else:
            yield buf + " "
            buf = s
    if buf:
        yield buf + " "


async def _drain_generation_chat(
    *,
    settings: Settings,
    model: str,
    messages: list[dict[str, str]],
    attempt_index: int,
    stream_stats: dict[str, Any],
    log_request: bool,
) -> str:
    """Stream one OpenAI completion to completion and return the joined text.

    Reasoning-family models (gpt-5, o-series) consume ``max_completion_tokens`` on internal
    reasoning before any visible content; the cap and per-attempt nudge here have to leave
    headroom for both. Classic chat models (gpt-4o-mini, etc.) ignore the extra room cheaply,
    so a single, reasoning-friendly upper bound works for all OpenAI models we target.
    """
    opts = {
        "temperature": min(0.6, settings.openai_temperature + 0.05 * attempt_index),
        "top_p": settings.openai_top_p,
        "num_predict": min(
            4096, settings.openai_max_completion_tokens + 256 * attempt_index
        ),
    }
    parts: list[str] = []
    async for piece in stream_openai_chat(
        base_url=settings.openai_base_url,
        model=model,
        api_key=settings.openai_api_key,
        messages=messages,
        timeout=openai_stream_timeout(settings),
        options=opts,
        stream_stats=stream_stats,
        log_request=log_request,
    ):
        parts.append(piece)
    return "".join(parts)


async def stream_guidance_events(
    conn: sqlite3.Connection,
    *,
    request: GuidanceRequest,
    settings: Settings,
) -> AsyncIterator[GuidanceStreamEvent]:
    """
    SSE contract:
    1. ``metadata`` — query, model name, verse count
    2. ``verses`` — exact DB verse cards (source of truth)
    3. ``token`` — explanation chunks (only after retrieval; never mutates verse text)
    4. ``error`` — optional if generation fails after verses (``code``, ``message``, ``fallback_used``)
    5. ``token`` — one short fallback paragraph when (4) occurs
    6. ``completed`` — stream finished (may include ``generation_attempts``, ``used_fallback_explanation``,
       ``latency_ms`` stage timings for observability)
    """
    t0 = time.perf_counter()
    latency_ms: dict[str, Any] = {
        "retrieval_ms": 0,
        "through_verses_sse_ms": 0,
        "first_token_ms_from_request_start": None,
        "generation_sum_ms": 0,
        "polish_validate_sum_ms": 0,
        "finalize_after_last_generation_ms": 0,
        "generation_last_stream_wall_ms": None,
        "first_explanation_sse_ms_from_request_start": None,
        "explanation_emit_ms": 0,
        "generation_attempts": 0,
        "retry_extra_attempts": 0,
        "total_request_ms": None,
        "completion_outcome": "success",
    }

    verses = await retrieve_verses_for_query(conn, query=request.query, settings=settings)
    verses = rank_verses_by_intent_and_fit(request.query, verses)
    verses = apply_theme_ordered_pins(request.query, verses)
    if len(verses) > settings.final_verse_count:
        verses = verses[: settings.final_verse_count]
    cards = _verse_cards(verses)
    latency_ms["retrieval_ms"] = int((time.perf_counter() - t0) * 1000)
    selected_model, rollout_bucket = _select_generation_model(settings, query=request.query)
    eval_debug = bool(request.eval_debug or settings.guidance_eval_debug)

    yield GuidanceStreamEvent(
        event="metadata",
        data={
            "query": request.query,
            "model": selected_model,
            "verse_count": len(verses),
            "eval_debug": bool(request.eval_debug or settings.guidance_eval_debug),
        },
    )
    yield GuidanceStreamEvent(
        event="verses",
        data={"verses": [c.model_dump() for c in cards]},
    )
    latency_ms["through_verses_sse_ms"] = int((time.perf_counter() - t0) * 1000)
    _log.info("guidance_retrieval", extra={"verse_count": len(verses)})

    if not verses:
        static_no_match = (
            "No verses in your local corpus matched this question, so there are no verse cards. "
            "This app only shows Bhagavad Gita text that exists in the database—nothing is invented. "
            "Try different wording, or seed/load verse data on the server (for example "
            "`make load-sample-data` from the backend folder), then ask again."
        )
        yield GuidanceStreamEvent(
            event="token",
            data={
                "text": (
                    "No verses were retrieved for this question, so there are no scripture cards below.\n\n"
                )
            },
        )

        use_openai = bool(
            settings.guidance_openai_when_no_verses and (settings.openai_api_key or "").strip()
        )
        attempts_used = 0
        gen_stats: dict[str, Any] = {}

        if use_openai:
            attempts_used = 1
            try:
                async with asyncio.timeout(settings.openai_generation_deadline_s):
                    gen_stats = {}
                    t_gen0 = time.perf_counter()
                    raw = await _drain_generation_chat(
                        settings=settings,
                        model=selected_model,
                        messages=build_no_verses_general_messages(query=request.query),
                        attempt_index=0,
                        stream_stats=gen_stats,
                        log_request=eval_debug,
                    )
                    latency_ms["generation_sum_ms"] = int((time.perf_counter() - t_gen0) * 1000)
                    latency_ms["generation_last_stream_wall_ms"] = gen_stats.get("openai_stream_wall_ms")
                    fc = gen_stats.get("first_chunk_latency_ms")
                    if isinstance(fc, int):
                        latency_ms["first_token_ms_from_request_start"] = int(
                            (t_gen0 - t0) * 1000
                        ) + fc
                    text = (raw or "").strip()
                    if text:
                        latency_ms["first_explanation_sse_ms_from_request_start"] = int(
                            (time.perf_counter() - t0) * 1000
                        )
                        t_sse0 = time.perf_counter()
                        delay_s = settings.guidance_stream_chunk_delay_s
                        for chunk in _iter_explanation_sse_chunks(text):
                            yield GuidanceStreamEvent(event="token", data={"text": chunk})
                            if delay_s > 0:
                                await asyncio.sleep(delay_s)
                        latency_ms["explanation_emit_ms"] = int((time.perf_counter() - t_sse0) * 1000)
                        latency_ms["completion_outcome"] = "no_matching_verses_general"
                    else:
                        yield GuidanceStreamEvent(event="token", data={"text": static_no_match})
                        latency_ms["completion_outcome"] = "no_matching_verses_static"
            except TimeoutError:
                yield GuidanceStreamEvent(
                    event="token",
                    data={"text": static_no_match},
                )
                latency_ms["completion_outcome"] = "no_matching_verses_openai_deadline"
            except OpenAIError:
                yield GuidanceStreamEvent(
                    event="token",
                    data={"text": static_no_match},
                )
                latency_ms["completion_outcome"] = "no_matching_verses_openai_error"
        else:
            yield GuidanceStreamEvent(event="token", data={"text": static_no_match})
            latency_ms["completion_outcome"] = "no_matching_verses_static"

        latency_ms["total_request_ms"] = int((time.perf_counter() - t0) * 1000)
        latency_ms["generation_attempts"] = attempts_used
        yield GuidanceStreamEvent(
            event="completed",
            data={
                "generation_attempts": attempts_used,
                "used_fallback_explanation": False,
                "latency_ms": latency_ms,
            },
        )
        _log.info("guidance_stream_completed", extra={"latency_ms": latency_ms})
        return

    profile = analyze_query(request.query)
    wants_two = wants_two_verse_generation(request.query)
    # Burnout defaults to a narrow budget; explicit "two verses / deeper answer" still upgrades
    # to two verses in the generation prompt when the corpus provides a second distinct pick.
    if profile.burnout:
        gen_max = settings.guidance_burnout_generation_max_verses
    else:
        gen_max = settings.guidance_generation_max_verses
    if wants_two:
        gen_max = max(gen_max, 2)
    gen_max = min(2, max(1, gen_max))
    gen_verses = select_verses_for_generation(
        request.query,
        verses,
        max_verses=gen_max,
    )
    primary_key = gen_verses[0].citation_key if gen_verses else ""
    supporting_key = gen_verses[1].citation_key if len(gen_verses) > 1 else None
    allowed = {v.citation_key for v in gen_verses}

    messages: list[dict[str, str]] = build_guidance_messages(
        query=request.query,
        verses=gen_verses,
        distress=profile.distress,
        primary_citation_key=primary_key or None,
        supporting_citation_key=supporting_key,
    )
    latency_ms.update(_generation_prompt_telemetry(messages))
    latency_ms["verses_in_generation_context"] = len(gen_verses)
    latency_ms["generation_max_verses_budget"] = gen_max
    latency_ms["query_profile_burnout"] = profile.burnout

    eval_info = _empty_eval_debug()
    eval_info["eval_debug"] = eval_debug
    if eval_debug:
        eval_info["openai_base_url"] = settings.openai_base_url
        eval_info["openai_model"] = selected_model

    attempts_used = 0
    used_fallback = False
    best_text = ""
    gen_stats: dict[str, Any] = {}
    validation_failures_count = 0
    user_visible_error = False

    try:
        async with asyncio.timeout(settings.openai_generation_deadline_s):
            delay_s = settings.guidance_stream_chunk_delay_s
            max_try = settings.guidance_validation_max_retries
            min_words = settings.guidance_validation_min_words
            max_words = settings.guidance_validation_max_words
            max_sentences = settings.guidance_validation_max_sentences

            for attempt in range(max_try):
                attempts_used = attempt + 1
                gen_stats = {}
                t_gen0 = time.perf_counter()
                raw = await _drain_generation_chat(
                    settings=settings,
                    model=selected_model,
                    messages=messages,
                    attempt_index=attempt,
                    stream_stats=gen_stats,
                    log_request=eval_debug,
                )
                t_gen1 = time.perf_counter()
                latency_ms["generation_sum_ms"] += int((t_gen1 - t_gen0) * 1000)
                if attempt == 0:
                    fc = gen_stats.get("first_chunk_latency_ms")
                    if isinstance(fc, int):
                        latency_ms["first_token_ms_from_request_start"] = int(
                            (t_gen0 - t0) * 1000
                        ) + fc
                        if fc >= 12_000:
                            _log.warning(
                                "guidance_slow_first_token",
                                extra={
                                    "first_chunk_latency_ms": fc,
                                    "generation_estimated_input_tokens": latency_ms.get(
                                        "generation_estimated_input_tokens"
                                    ),
                                    "generation_prompt_chars": latency_ms.get("generation_prompt_chars"),
                                    "verses_in_generation_context": latency_ms.get(
                                        "verses_in_generation_context"
                                    ),
                                    "verse_count_shown": len(verses),
                                    "query_profile_burnout": profile.burnout,
                                    "query_profile_distress": profile.distress,
                                    "query_preview": (
                                        (request.query[:120] + "…")
                                        if len(request.query) > 120
                                        else request.query
                                    ),
                                },
                            )

                t_pv0 = time.perf_counter()
                polished = polish_guidance_full_text(
                    raw.strip(),
                    allowed_citation_keys=allowed,
                    primary_citation_key=primary_key or None,
                )
                if polished and primary_key:
                    polished = _render_primary_citation_deterministically(
                        polished,
                        primary_citation_key=primary_key,
                    )
                vr = validate_guidance_explanation(
                    polished,
                    primary_citation_key=primary_key,
                    allowed=allowed,
                    profile=profile,
                    min_words=min_words,
                    max_words=max_words,
                    max_sentences=max_sentences,
                )
                latency_ms["polish_validate_sum_ms"] += int((time.perf_counter() - t_pv0) * 1000)
                best_text = polished
                if vr.ok:
                    break
                _log.info(
                    "guidance_validation_failed",
                    extra={"attempt": attempt, "reasons": list(vr.reasons)},
                )
                validation_failures_count += 1
                if attempt + 1 < max_try:
                    repair = build_regeneration_instruction(vr.reasons, primary_citation_key=primary_key)
                    messages = [
                        *messages,
                        {"role": "assistant", "content": polished},
                        {"role": "user", "content": repair},
                    ]

            eval_info.update(gen_stats)
            latency_ms["generation_last_stream_wall_ms"] = gen_stats.get("openai_stream_wall_ms")

            if profile.burnout and settings.guidance_burnout_debug_log:
                user_msg_preview = ""
                for m in messages:
                    if m.get("role") == "user":
                        uc = m.get("content") or ""
                        user_msg_preview = uc[:600].replace("\n", " ")
                        break
                _log.info(
                    "guidance_burnout_debug",
                    extra={
                        "primary_citation_key": primary_key,
                        "allowed": sorted(allowed),
                        "verses_in_generation_context": len(gen_verses),
                        "generation_max_verses_budget": gen_max,
                        "generation_prompt_chars": latency_ms.get("generation_prompt_chars"),
                        "generation_estimated_input_tokens": latency_ms.get(
                            "generation_estimated_input_tokens"
                        ),
                        "first_chunk_latency_ms": gen_stats.get("first_chunk_latency_ms"),
                        "openai_stream_wall_ms": gen_stats.get("openai_stream_wall_ms"),
                        "attempts_used": attempts_used,
                        "user_prompt_preview": user_msg_preview,
                    },
                )

            t_finalize0 = time.perf_counter()
            final_vr = validate_guidance_explanation(
                best_text,
                primary_citation_key=primary_key,
                allowed=allowed,
                profile=profile,
                min_words=min_words,
                max_words=max_words,
                max_sentences=max_sentences,
            )

            if best_text.strip() and not final_vr.ok:
                trimmed = trim_explanation_to_limits(
                    best_text,
                    max_words=max_words,
                    max_sentences=max_sentences,
                )
                if trimmed:
                    tr_vr = validate_guidance_explanation(
                        trimmed,
                        primary_citation_key=primary_key,
                        allowed=allowed,
                        profile=profile,
                        min_words=min_words,
                        max_words=max_words,
                        max_sentences=max_sentences,
                    )
                    if tr_vr.ok:
                        best_text = trimmed
                        final_vr = tr_vr

            if best_text.strip() and primary_key:
                deterministic = _render_primary_citation_deterministically(
                    best_text,
                    primary_citation_key=primary_key,
                )
                if deterministic != best_text:
                    re_vr = validate_guidance_explanation(
                        deterministic,
                        primary_citation_key=primary_key,
                        allowed=allowed,
                        profile=profile,
                        min_words=min_words,
                        max_words=max_words,
                        max_sentences=max_sentences,
                    )
                    if re_vr.ok:
                        best_text = deterministic
                        final_vr = re_vr

            # Structured-citation salvage: if the only problems are citation-shape issues
            # (missing permissive mention, missing exact label, malformed chapter-only ref,
            # truncated inline ref like ``—2.Act``), inject the canonical label so the copy
            # does not fall through to fallback for a purely cosmetic citation miss.
            _CITATION_ONLY_REASONS = {
                "missing_primary_citation",
                "missing_primary_citation_label",
                "malformed_verse_reference",
                "orphan_leading_bare_citation",
                "inline_truncated_chapter_ref",
            }
            if (
                best_text.strip()
                and not final_vr.ok
                and primary_key
                and set(final_vr.reasons).issubset(_CITATION_ONLY_REASONS)
            ):
                salvage_candidate = normalize_primary_citation_label(
                    best_text, primary_citation_key=primary_key
                )
                salvage_candidate = enforce_primary_citation_label(
                    salvage_candidate, primary_citation_key=primary_key
                )
                salvage_candidate = salvage_missing_primary_citation(
                    salvage_candidate, primary_citation_key=primary_key
                )
                if salvage_candidate and salvage_candidate != best_text:
                    sv_vr = validate_guidance_explanation(
                        salvage_candidate,
                        primary_citation_key=primary_key,
                        allowed=allowed,
                        profile=profile,
                        min_words=min_words,
                        max_words=max_words,
                        max_sentences=max_sentences,
                    )
                    if sv_vr.ok:
                        _log.info(
                            "guidance_salvaged_structured_citation",
                            extra={
                                "primary_citation_key": primary_key,
                                "reasons_before": list(final_vr.reasons),
                            },
                        )
                        best_text = salvage_candidate
                        final_vr = sv_vr

            if not best_text.strip() or not final_vr.ok:
                if eval_debug:
                    eval_info["validation_final_reasons"] = list(final_vr.reasons)
                    eval_info["last_polished_rejected"] = best_text
                    eval_info["fallback_reason"] = (
                        "validation_failed_empty_polished"
                        if not best_text.strip()
                        else "validation_failed"
                    )
                else:
                    eval_info["fallback_reason"] = "validation_fallback_product"
                # Never stream a failed draft. Profile-aware: distress/grief → soft template;
                # non-sensitive → verse-specific fallback so copy stays tied to the verse.
                best_text = deterministic_fallback_explanation(
                    primary_citation_key=primary_key,
                    distress=profile.distress,
                    surrender_explicit=profile.surrender_explicit,
                )
                if primary_key:
                    best_text = enforce_primary_citation_label(
                        best_text, primary_citation_key=primary_key
                    )
                used_fallback = True
                eval_info["used_validation_rejected_draft"] = False

            latency_ms["finalize_after_last_generation_ms"] = int(
                (time.perf_counter() - t_finalize0) * 1000
            )

            if best_text.strip():
                latency_ms["first_explanation_sse_ms_from_request_start"] = int(
                    (time.perf_counter() - t0) * 1000
                )
                t_sse0 = time.perf_counter()
                for chunk in _iter_explanation_sse_chunks(best_text):
                    yield GuidanceStreamEvent(event="token", data={"text": chunk})
                    if delay_s > 0:
                        await asyncio.sleep(delay_s)
                latency_ms["explanation_emit_ms"] = int((time.perf_counter() - t_sse0) * 1000)

    except TimeoutError:
        exc = OpenAIError(
            "Generation exceeded the configured time limit. Verses shown above remain valid.",
            code="openai_deadline",
        )
        eval_info.update(gen_stats)
        eval_info["raw_error"] = f"{type(exc).__name__}: {exc}"
        eval_info["fallback_reason"] = exc.code
        _log.warning(
            "guidance_generation_deadline",
            extra={
                "code": exc.code,
                "generation_model": selected_model,
                "exc_traceback": traceback.format_exc() if eval_debug else None,
            },
        )
        latency_ms["completion_outcome"] = "openai_deadline"
        user_visible_error = True
        for ev in _fallback_events(exc, eval_debug=eval_debug):
            yield ev
    except OpenAIError as exc:
        eval_info.update(gen_stats)
        eval_info["raw_error"] = f"{type(exc).__name__}: {exc}"
        eval_info["fallback_reason"] = exc.code
        _log.warning(
            "guidance_generation_failed",
            extra={
                "code": exc.code,
                # "message" is reserved on logging.LogRecord; use a distinct key.
                "generation_error_message": exc.message,
                "generation_model": selected_model,
                "openai_http_status": gen_stats.get("openai_http_status"),
                "exc_traceback": traceback.format_exc() if eval_debug else None,
            },
        )
        latency_ms["completion_outcome"] = "openai_error"
        user_visible_error = True
        for ev in _fallback_events(exc, eval_debug=eval_debug):
            yield ev

    latency_ms["total_request_ms"] = int((time.perf_counter() - t0) * 1000)
    latency_ms["generation_attempts"] = attempts_used
    latency_ms["retry_extra_attempts"] = max(0, attempts_used - 1)

    completed_data: dict[str, Any] = {
        "generation_attempts": attempts_used,
        "used_fallback_explanation": used_fallback,
        "latency_ms": latency_ms,
    }
    if eval_debug:
        completed_data["eval"] = eval_info
    _log.info("guidance_stream_completed", extra={"latency_ms": latency_ms})
    cumulative = _record_prod_metrics(
        used_fallback=used_fallback,
        validation_failures=validation_failures_count,
        user_visible_error=user_visible_error,
    )
    _log.info(
        "guidance_prod_observability",
        extra={
            "model": selected_model,
            "rollout_bucket": rollout_bucket,
            "rollout_primary_percent": settings.guidance_primary_model_rollout_percent,
            "query_preview": (request.query[:96] + "…") if len(request.query) > 96 else request.query,
            "used_fallback_explanation": used_fallback,
            "validation_failures_count": validation_failures_count,
            "user_visible_error": user_visible_error,
            "latency_total_ms": latency_ms.get("total_request_ms"),
            "latency_first_token_ms": latency_ms.get("first_token_ms_from_request_start"),
            "completion_outcome": latency_ms.get("completion_outcome"),
            "fallback_total": cumulative["fallback_total"],
            "validation_failures_total": cumulative["validation_failures_total"],
            "user_visible_errors_total": cumulative["user_visible_errors_total"],
            "requests_total": cumulative["requests_total"],
        },
    )
    yield GuidanceStreamEvent(event="completed", data=completed_data)
