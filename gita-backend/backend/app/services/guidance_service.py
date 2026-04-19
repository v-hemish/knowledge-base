from __future__ import annotations

import asyncio
import logging
import re
import sqlite3
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
from app.llm.ollama_client import OllamaError, ollama_stream_timeout, stream_ollama_chat
from app.llm.prompts import build_guidance_messages
from app.llm.query_intent import analyze_query, rank_verses_by_intent_and_fit, select_verses_for_generation
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


def _fallback_events(exc: OllamaError, *, eval_debug: bool) -> Iterator[GuidanceStreamEvent]:
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
        "ollama_http_status": None,
        "ollama_response_body_snippet": None,
        "ollama_stream_error_line": None,
        "validation_final_reasons": None,
        "last_polished_rejected": None,
        "used_validation_rejected_draft": False,
    }


def _generation_prompt_telemetry(messages: list[dict[str, str]]) -> dict[str, int]:
    """Rough input size for Ollama (chars + ~token estimate) without calling the tokenizer."""
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


async def _drain_ollama_chat(
    *,
    settings: Settings,
    messages: list[dict[str, str]],
    attempt_index: int,
    stream_stats: dict[str, Any],
    log_request: bool,
) -> str:
    opts = {
        "temperature": min(0.28, settings.ollama_temperature + 0.04 * attempt_index),
        "top_p": max(0.58, settings.ollama_top_p - 0.015 * attempt_index),
        "repeat_penalty": settings.ollama_repeat_penalty,
        "num_predict": min(145, settings.ollama_num_predict + 15 * attempt_index),
    }
    parts: list[str] = []
    async for piece in stream_ollama_chat(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        messages=messages,
        timeout=ollama_stream_timeout(settings),
        options=opts,
        stream_stats=stream_stats,
        log_request=log_request,
        keep_alive=(settings.ollama_keep_alive or None),
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
        "first_ollama_token_ms_from_request_start": None,
        "ollama_generation_sum_ms": 0,
        "polish_validate_sum_ms": 0,
        "finalize_after_last_ollama_ms": 0,
        "ollama_last_stream_wall_ms": None,
        "first_explanation_sse_ms_from_request_start": None,
        "explanation_emit_ms": 0,
        "generation_attempts": 0,
        "retry_extra_attempts": 0,
        "ollama_seconds_since_previous_stream_end": None,
        "total_request_ms": None,
        "completion_outcome": "success",
    }

    verses = await retrieve_verses_for_query(conn, query=request.query, settings=settings)
    verses = rank_verses_by_intent_and_fit(request.query, verses)
    cards = _verse_cards(verses)
    latency_ms["retrieval_ms"] = int((time.perf_counter() - t0) * 1000)

    yield GuidanceStreamEvent(
        event="metadata",
        data={
            "query": request.query,
            "ollama_model": settings.ollama_model,
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
        yield GuidanceStreamEvent(
            event="token",
            data={
                "text": (
                    "No matching verses were found in the local database. "
                    "Try different wording, or confirm the corpus is seeded."
                )
            },
        )
        latency_ms["total_request_ms"] = int((time.perf_counter() - t0) * 1000)
        latency_ms["completion_outcome"] = "no_matching_verses"
        yield GuidanceStreamEvent(
            event="completed",
            data={
                "generation_attempts": 0,
                "used_fallback_explanation": False,
                "latency_ms": latency_ms,
            },
        )
        _log.info("guidance_stream_completed", extra={"latency_ms": latency_ms})
        return

    profile = analyze_query(request.query)
    # Burnout gets a dedicated verse budget; everything else uses the default. Keeps the
    # burnout-latency fix narrow (no effect on duty_outcomes, discipline, grief, etc.).
    gen_max = (
        settings.guidance_burnout_generation_max_verses
        if profile.burnout
        else settings.guidance_generation_max_verses
    )
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

    eval_debug = bool(request.eval_debug or settings.guidance_eval_debug)
    eval_info = _empty_eval_debug()
    eval_info["eval_debug"] = eval_debug
    if eval_debug:
        eval_info["ollama_base_url"] = settings.ollama_base_url

    attempts_used = 0
    used_fallback = False
    best_text = ""
    ollama_stats: dict[str, Any] = {}

    try:
        async with asyncio.timeout(settings.ollama_generation_deadline_s):
            delay_s = settings.guidance_stream_chunk_delay_s
            max_try = settings.guidance_validation_max_retries
            min_words = settings.guidance_validation_min_words
            max_words = settings.guidance_validation_max_words
            max_sentences = settings.guidance_validation_max_sentences

            for attempt in range(max_try):
                attempts_used = attempt + 1
                ollama_stats = {}
                t_ollama0 = time.perf_counter()
                raw = await _drain_ollama_chat(
                    settings=settings,
                    messages=messages,
                    attempt_index=attempt,
                    stream_stats=ollama_stats,
                    log_request=eval_debug,
                )
                t_ollama1 = time.perf_counter()
                latency_ms["ollama_generation_sum_ms"] += int((t_ollama1 - t_ollama0) * 1000)
                latency_ms["ollama_seconds_since_previous_stream_end"] = ollama_stats.get(
                    "ollama_seconds_since_previous_stream_end"
                )
                if attempt == 0:
                    fc = ollama_stats.get("first_chunk_latency_ms")
                    if isinstance(fc, int):
                        latency_ms["first_ollama_token_ms_from_request_start"] = int(
                            (t_ollama0 - t0) * 1000
                        ) + fc
                        if fc >= 12_000:
                            # Long first-token waits are dominated by Ollama (load/queue/GPU), not
                            # prompt bytes alone—investigate with ollama_seconds_since_previous_stream_end
                            # and server load separately from prompt-trim experiments.
                            _log.warning(
                                "guidance_ollama_slow_first_token",
                                extra={
                                    "first_chunk_latency_ms": fc,
                                    "ollama_seconds_since_previous_stream_end": ollama_stats.get(
                                        "ollama_seconds_since_previous_stream_end"
                                    ),
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
                if attempt + 1 < max_try:
                    repair = build_regeneration_instruction(vr.reasons, primary_citation_key=primary_key)
                    messages = [
                        *messages,
                        {"role": "assistant", "content": polished},
                        {"role": "user", "content": repair},
                    ]

            eval_info.update(ollama_stats)
            latency_ms["ollama_last_stream_wall_ms"] = ollama_stats.get("ollama_stream_wall_ms")

            if profile.burnout and settings.guidance_burnout_debug_log:
                # Dedicated telemetry for the burnout path. Lets us compare burnout against the
                # other prompts without enabling verbose logs globally. Prompt preview is a head
                # of the *user* content only (the system prompt is a fixed template and is not
                # logged verbatim).
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
                        "first_chunk_latency_ms": ollama_stats.get("first_chunk_latency_ms"),
                        "ollama_stream_wall_ms": ollama_stats.get("ollama_stream_wall_ms"),
                        "ollama_seconds_since_previous_stream_end": ollama_stats.get(
                            "ollama_seconds_since_previous_stream_end"
                        ),
                        "first_after_idle": ollama_stats.get(
                            "ollama_seconds_since_previous_stream_end"
                        )
                        is None,
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

            # Structured-citation salvage: if the only problems are citation-shape issues
            # (missing permissive mention, missing exact label, malformed chapter-only ref),
            # inject the canonical ``Bhagavad Gita <pk>`` label from the structured field so the
            # copy does not fall through to fallback for a purely cosmetic citation miss.
            _CITATION_ONLY_REASONS = {
                "missing_primary_citation",
                "missing_primary_citation_label",
                "malformed_verse_reference",
                "orphan_leading_bare_citation",
            }
            if (
                best_text.strip()
                and not final_vr.ok
                and primary_key
                and set(final_vr.reasons).issubset(_CITATION_ONLY_REASONS)
            ):
                # Deterministic citation repair: scrub any malformed fragments and inject the
                # exact structured label. This is the primary mechanism that rescues drafts
                # whose only problem is the model mis-rendering the citation string.
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
                # non-sensitive (duty_outcomes, discipline, etc.) → verse-specific fallback so
                # copy stays tied to the selected verse, not a generic "read slowly" line.
                best_text = deterministic_fallback_explanation(
                    primary_citation_key=primary_key,
                    distress=profile.distress,
                    surrender_explicit=profile.surrender_explicit,
                )
                # Defense in depth: fallback copy already contains ``Bhagavad Gita <pk>`` by
                # construction, but running enforcement keeps a single invariant — every code
                # path that produces ``best_text`` for streaming exits with the exact label.
                if primary_key:
                    best_text = enforce_primary_citation_label(
                        best_text, primary_citation_key=primary_key
                    )
                used_fallback = True
                eval_info["used_validation_rejected_draft"] = False

            latency_ms["finalize_after_last_ollama_ms"] = int((time.perf_counter() - t_finalize0) * 1000)

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
        exc = OllamaError(
            "Generation exceeded the configured time limit. Verses shown above remain valid.",
            code="ollama_deadline",
        )
        eval_info.update(ollama_stats)
        eval_info["raw_error"] = f"{type(exc).__name__}: {exc}"
        eval_info["fallback_reason"] = exc.code
        _log.warning(
            "guidance_ollama_deadline",
            extra={
                "code": exc.code,
                "ollama_model": settings.ollama_model,
                "exc_traceback": traceback.format_exc() if eval_debug else None,
            },
        )
        latency_ms["completion_outcome"] = "ollama_deadline"
        for ev in _fallback_events(exc, eval_debug=eval_debug):
            yield ev
    except OllamaError as exc:
        eval_info.update(ollama_stats)
        eval_info["raw_error"] = f"{type(exc).__name__}: {exc}"
        eval_info["fallback_reason"] = exc.code
        _log.warning(
            "guidance_ollama_failed",
            extra={
                "code": exc.code,
                # "message" is reserved on logging.LogRecord; use a distinct key.
                "ollama_error_message": exc.message,
                "ollama_model": settings.ollama_model,
                "ollama_base_url": settings.ollama_base_url,
                "ollama_http_status": ollama_stats.get("ollama_http_status"),
                "exc_traceback": traceback.format_exc() if eval_debug else None,
            },
        )
        latency_ms["completion_outcome"] = "ollama_error"
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
    yield GuidanceStreamEvent(event="completed", data=completed_data)
