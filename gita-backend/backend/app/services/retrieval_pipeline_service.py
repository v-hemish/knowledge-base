"""Two-stage retrieval: lexical recall (FTS5) then optional semantic rerank (precomputed embeddings)."""

from __future__ import annotations

import asyncio
import logging
import sqlite3

from app.core.config import Settings
from app.db.verses_repo import fetch_verses_by_citation_keys, fetch_verses_by_ids
from app.llm.theme_routing import prepend_theme_canonical_verses
from app.models.verse import Verse
from app.retrieval.citation_query import citation_key_from_retrieval_query
from app.retrieval.cosine_reranker import rerank_with_index
from app.retrieval.embedding_store import get_embedding_index
from app.retrieval.query_expansion import expanded_retrieval_query
from app.retrieval.lexical import LexicalCandidate
from app.retrieval.selection import VerseWithRetrievalMeta
from app.services.lexical_retrieval_service import LexicalRetrievalService

_log = logging.getLogger(__name__)


class RetrievalPipelineService:
    """
    1) Lexical candidates (BM25-ordered ids)
    2) Fetch verse rows
    3) Optional cosine rerank using startup-loaded embedding matrix + query encoder
    4) Up to ``fts_candidate_limit`` verses for downstream intent/theme ordering (UI caps later)

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
        rq = expanded_retrieval_query(query)
        hits = await asyncio.to_thread(
            lambda: self._lexical.search(conn, query=rq, settings=settings),
        )
        cite = citation_key_from_retrieval_query(query)
        if cite:
            by_cite = await asyncio.to_thread(lambda: fetch_verses_by_citation_keys(conn, [cite]))
            row = by_cite.get(cite)
            if row is not None:
                syn = LexicalCandidate(
                    verse_id=row.id,
                    chapter=row.chapter,
                    verse=row.verse,
                    citation_key=row.citation_key,
                    translation=row.translation,
                    retrieval_score=1e12,
                    matched_by=("citation_query",),
                )
                hits = [h for h in hits if h.verse_id != syn.verse_id]
                hits.insert(0, syn)
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
                    return rerank_with_index(rq, verses, settings=settings, index=idx)

                try:
                    verses = await asyncio.to_thread(_rerank)
                    sem_applied = True
                except Exception:
                    _log.exception("semantic_rerank_failed_lexical_fallback")

        verses = prepend_theme_canonical_verses(conn, query, verses)
        # Keep the full lexical (+ optional semantic) candidate pool for downstream
        # intent boosts and theme pins; guidance caps to ``final_verse_count`` after reordering.
        pool = verses[: settings.fts_candidate_limit]
        out: list[VerseWithRetrievalMeta] = []
        for pos, v in enumerate(pool, start=1):
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
