"""Guidance endpoints: non-streaming retrieval and SSE streaming explanations."""

from __future__ import annotations

import sqlite3
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps import (
    check_guidance_rate_limit,
    check_guidance_retrieve_rate_limit,
    get_db_conn,
    get_settings_dep,
)
from app.core.config import Settings
from app.schemas.guidance import GuidanceFeedbackRequest, GuidanceRequest
from app.schemas.guidance_retrieve import RetrieveGuidanceResponse
from app.services.answer_assembler import AnswerAssemblerService
from app.services.guidance_feedback_log import append_guidance_feedback, feedback_record
from app.services.guidance_service import stream_guidance_events
from app.utils.sse import sse_data_line

router = APIRouter(tags=["guidance"])

_assembler = AnswerAssemblerService()


@router.post("/guidance/feedback")
async def guidance_feedback(
    body: GuidanceFeedbackRequest,
    request: Request,
    _rate_ok: None = Depends(check_guidance_rate_limit),
    settings: Settings = Depends(get_settings_dep),
) -> dict[str, bool | str | None]:
    """
    Record lightweight user feedback (NDJSON append). Disabled unless ``GUIDANCE_FEEDBACK_LOG_PATH`` is set.

    Intended for beta: thumbs-down with optional notes to review later. No verse or model payload is stored
    unless the client includes it in ``notes`` (keep ``notes`` short; avoid pasting full explanations with PII).
    """
    log_path = settings.resolved_guidance_feedback_log_path()
    if log_path is None:
        return {"accepted": False, "reason": "feedback_logging_disabled"}

    rid = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    rec = feedback_record(
        rating=body.rating,
        notes=body.notes,
        client_stream_id=body.client_stream_id,
        request_id=rid,
    )
    append_guidance_feedback(log_path, rec)
    return {"accepted": True, "reason": None}


@router.post("/guidance/retrieve", response_model=RetrieveGuidanceResponse)
async def guidance_retrieve(
    body: GuidanceRequest,
    _rate_ok: None = Depends(check_guidance_retrieve_rate_limit),
    conn: sqlite3.Connection = Depends(get_db_conn),
    settings: Settings = Depends(get_settings_dep),
) -> RetrieveGuidanceResponse:
    """
    Return one to three verse cards from SQLite only (no LLM).

    **Request (JSON body)**

    ```json
    {"query": "How do I act without attachment to results?"}
    ```

    **Response (abbreviated)**

    ```json
    {
      "query": "How do I act without attachment to results?",
      "selected_verses": [
        {
          "citation_key": "2.47",
          "chapter": 2,
          "verse": 47,
          "sanskrit": null,
          "transliteration": null,
          "translation": "...",
          "why_selected_short": "Matched translation / themes; reranked by semantic similarity."
        }
      ],
      "reflection_prompt": null,
      "explanation_status": "verses_only"
    }
    ```

    FUTURE: optional ``include_scores`` for debugging.
    """
    return await _assembler.build_retrieve_response(conn, query=body.query, settings=settings)


@router.post("/guidance/stream")
async def guidance_stream(
    body: GuidanceRequest,
    _rate_ok: None = Depends(check_guidance_rate_limit),
    conn: sqlite3.Connection = Depends(get_db_conn),
    settings: Settings = Depends(get_settings_dep),
) -> StreamingResponse:
    """
    Server-Sent Events stream: verse cards first, then explanation tokens from the LLM.

    **Request (JSON body)**

    ```json
    {"query": "What does Krishna say about duty and fear?"}
    ```

    **SSE shape** — each ``data:`` line is one JSON object with ``event`` and ``data``:

    1. ``metadata`` — ``query``, ``model``, ``verse_count``
    2. ``verses`` — ``{"verses": [ ... VerseCard ... ]}`` (database text only)
    3. ``token`` — ``{"text": "..."}`` repeated for streamed explanation
    4. ``error`` — optional if generation fails after verses (``code``, ``message``, ``fallback_used``)
    5. ``token`` — short fallback text when (4) occurred
    6. ``completed`` — stream finished

    **Example first lines (conceptual)**

    ```
    data: {"event":"metadata","data":{"query":"...","model":"gpt-5-mini","verse_count":2}}
    data: {"event":"verses","data":{"verses":[...]}}
    data: {"event":"token","data":{"text":"In this passage"}}
    ```

    FUTURE: optional ``Accept: application/json`` non-streaming mode for low-latency clients.
    """

    async def events() -> AsyncIterator[str]:
        async for ev in stream_guidance_events(conn, request=body, settings=settings):
            yield sse_data_line(ev.model_dump_json())

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
