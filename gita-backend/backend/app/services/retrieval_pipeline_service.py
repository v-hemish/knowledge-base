"""Two-stage retrieval: lexical recall (FTS5) then optional semantic rerank (precomputed embeddings)."""

from __future__ import annotations

import asyncio
import logging
import sqlite3

from app.core.config import Settings
from app.db.verses_repo import fetch_verses_by_ids
from app.models.verse import Verse
from app.retrieval.cosine_reranker import rerank_with_index
from app.retrieval.embedding_store import get_embedding_index
from app.retrieval.selection import VerseWithRetrievalMeta
from app.services.lexical_retrieval_service import LexicalRetrievalService

_log = logging.getLogger(__name__)


class RetrievalPipelineService:
    """
    1) Lexical candidates (BM25-ordered ids)
    2) Fetch verse rows
    3) Optional cosine rerank using startup-loaded embedding matrix + query encoder
    4) Top `final_verse_count` verses (1–3 by default)

    If embeddings are missing, models mismatch, or encoding fails, falls back to lexical order.
    """

    def __init__(self) -> None:
        self._lexical = LexicalRetrievalService()

    async def retrieve_with_metadata(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        settings: Settings,
    ) -> list[VerseWithRetrievalMeta]:
        hits = await asyncio.to_thread(
            lambda: self._lexical.search(conn, query=query, settings=settings),
        )
        if not hits:
            _log.info("retrieval_lexical_miss", extra={"query_len": len(query)})
            return []

        n_lex = len(hits)
        id_order = [h.verse_id for h in hits]
        hit_by_id = {h.verse_id: h for h in hits}
        rank_by_id = {h.verse_id: i + 1 for i, h in enumerate(hits)}

        def _fetch() -> list[Verse]:
            m = fetch_verses_by_ids(conn, id_order)
            return [m[i] for i in id_order if i in m]

        verses = await asyncio.to_thread(_fetch)
        if not verses:
            return []

        sem_applied = False
        if settings.semantic_rerank_enabled and len(verses) > 1:
            idx = get_embedding_index()
            if idx is None:
                _log.debug("semantic_rerank_skipped_no_embeddings")
            else:

                def _rerank() -> list[Verse]:
                    return rerank_with_index(query, verses, settings=settings, index=idx)

                try:
                    verses = await asyncio.to_thread(_rerank)
                    sem_applied = True
                except Exception:
                    _log.exception("semantic_rerank_failed_lexical_fallback")

        final = verses[: settings.final_verse_count]
        out: list[VerseWithRetrievalMeta] = []
        for pos, v in enumerate(final, start=1):
            hit = hit_by_id.get(v.id)
            matched = hit.matched_by if hit else ()
            score = float(hit.retrieval_score) if hit else 0.0
            lr = rank_by_id.get(v.id, 999)
            out.append(
                VerseWithRetrievalMeta(
                    verse=v,
                    lexical_rank=lr,
                    lexical_retrieval_score=score,
                    matched_by=matched,
                    semantic_rerank_applied=sem_applied,
                    final_position=pos,
                    total_lexical_candidates=n_lex,
                )
            )
        return out

    async def retrieve(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        settings: Settings,
    ) -> list[Verse]:
        metas = await self.retrieve_with_metadata(conn, query=query, settings=settings)
        return [m.verse for m in metas]
