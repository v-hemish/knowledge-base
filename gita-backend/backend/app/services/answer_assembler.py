"""Assemble API responses from DB-backed verses and retrieval metadata (no LLM for verse text)."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import replace

from app.core.config import Settings
from app.llm.query_intent import rank_verses_by_intent_and_fit
from app.llm.theme_routing import apply_theme_ordered_pins
from app.retrieval.selection import VerseWithRetrievalMeta
from app.schemas.guidance_retrieve import (
    ExplanationStatus,
    RetrieveGuidanceResponse,
    RetrieveVerseCard,
)
from app.services.retrieve_cache import retrieve_cache_get, retrieve_cache_set
from app.services.retrieval_pipeline_service import RetrievalPipelineService

_log = logging.getLogger(__name__)

_MAX_WHY_LEN = 280

_retrieval = RetrievalPipelineService()


def _retrieve_cache_key(query: str, settings: Settings) -> str:
    q = query.strip().casefold()
    return "|".join(
        (
            q,
            str(settings.final_verse_count),
            str(settings.fts_candidate_limit),
            "1" if settings.semantic_rerank_enabled else "0",
            str(settings.resolved_database_path()),
        )
    )


def compute_why_selected_short(meta: VerseWithRetrievalMeta) -> str:
    """
    Deterministic, human-readable line from lexical + optional semantic stages.
    FUTURE: localization and richer feature flags (e.g. show BM25 score).
    """
    if meta.matched_by:
        cols = ", ".join(meta.matched_by)
        head = f"Lexical match in {cols}"
    else:
        head = "Lexical match (FTS)"
    mid = f"stage-1 rank {meta.lexical_rank}/{meta.total_lexical_candidates}"
    tail = "stage-2 semantic rerank applied" if meta.semantic_rerank_applied else "stage-2 semantic rerank skipped"
    slot = f"returned order #{meta.final_position}"
    s = f"{head}; {mid}; {tail}; {slot}"
    if len(s) <= _MAX_WHY_LEN:
        return s
    return s[: _MAX_WHY_LEN - 3] + "..."


class AnswerAssemblerService:
    """Builds retrieve-only guidance payloads from the retrieval pipeline."""

    def __init__(self, retrieval: RetrievalPipelineService | None = None) -> None:
        self._retrieval = retrieval or _retrieval

    async def build_retrieve_response(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        settings: Settings,
    ) -> RetrieveGuidanceResponse:
        cache_key = _retrieve_cache_key(query, settings)
        cached = retrieve_cache_get(cache_key)
        if cached is not None:
            _log.debug("retrieve_cache_hit", extra={"cache_key_prefix": cache_key[:48]})
            return cached

        metas = await self._retrieval.retrieve_with_metadata(conn, query=query, settings=settings)
        if not metas:
            out = RetrieveGuidanceResponse(
                query=query,
                selected_verses=[],
                reflection_prompt=None,
                explanation_status="no_hits",
            )
            retrieve_cache_set(cache_key, out)
            return out

        verses = [m.verse for m in metas]
        verses = rank_verses_by_intent_and_fit(query, verses)
        verses = apply_theme_ordered_pins(query, verses)
        verses = verses[: settings.final_verse_count]
        meta_by_key = {m.verse.citation_key: m for m in metas}
        cards: list[RetrieveVerseCard] = []
        for pos, v in enumerate(verses, start=1):
            m = meta_by_key.get(v.citation_key)
            if m is None:
                m = VerseWithRetrievalMeta(
                    verse=v,
                    lexical_rank=999,
                    lexical_retrieval_score=0.0,
                    matched_by=("theme_canonical",),
                    semantic_rerank_applied=False,
                    final_position=pos,
                    total_lexical_candidates=len(metas),
                )
            else:
                m = replace(m, final_position=pos)
            cards.append(
                RetrieveVerseCard(
                    citation_key=v.citation_key,
                    chapter=v.chapter,
                    verse=v.verse,
                    sanskrit=v.sanskrit,
                    transliteration=v.transliteration,
                    translation=v.translation,
                    why_selected_short=compute_why_selected_short(m),
                )
            )

        if not cards:
            out = RetrieveGuidanceResponse(
                query=query,
                selected_verses=[],
                reflection_prompt=None,
                explanation_status="no_hits",
            )
            retrieve_cache_set(cache_key, out)
            return out

        reflection = (
            "You can request a brief streamed explanation with POST /api/v1/guidance/stream "
            "using the same query; verse wording always comes from the database first."
        )
        _log.info("retrieve_assembled", extra={"verse_count": len(cards)})
        out = RetrieveGuidanceResponse(
            query=query,
            selected_verses=cards,
            reflection_prompt=reflection,
            explanation_status="verses_only",
        )
        retrieve_cache_set(cache_key, out)
        return out
