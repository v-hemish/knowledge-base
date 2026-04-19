"""Lexical row-id bridge used by legacy call sites; delegates to `retrieval.lexical`."""

import sqlite3

from app.retrieval.lexical import lexical_search


def fts_row_ids(conn: sqlite3.Connection, raw_query: str, *, limit: int) -> list[int]:
    """Return verse row ids in BM25 order (same column scope as `lexical_search`)."""
    return [c.verse_id for c in lexical_search(conn, raw_query, limit=limit)]
