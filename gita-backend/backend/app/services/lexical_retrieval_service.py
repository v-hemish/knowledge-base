"""Application service for BM25 lexical verse retrieval (FTS5)."""

from __future__ import annotations

import sqlite3

from app.core.config import Settings
from app.retrieval.lexical import LexicalCandidate, lexical_search


class LexicalRetrievalService:
    """
    Thin service over `retrieval.lexical` — keeps HTTP routes free of SQL/MATCH details.
    FUTURE: inject telemetry, query rewriting, and per-user limits.
    """

    def search(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        settings: Settings,
    ) -> list[LexicalCandidate]:
        return self.search_with_limit(
            conn,
            query=query,
            limit=settings.fts_candidate_limit,
        )

    def search_with_limit(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        limit: int,
    ) -> list[LexicalCandidate]:
        return lexical_search(conn, query, limit=max(1, min(limit, 200)))
