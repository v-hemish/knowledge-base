"""
SQLite FTS5 lexical retrieval with BM25-style ranking.

Search is restricted to translation, transliteration, theme_tags, and situation_tags
(via MATCH column filters). Sanskrit and use_with_care_tags remain in the FTS index
for ingest consistency but are not used for user query matching here.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass

# Columns we score and report for lexical search (subset of verses_fts indexed fields).
_LEXICAL_COLUMNS = ("translation", "transliteration", "theme_tags", "situation_tags")

_TOKEN_RE = re.compile(r"[^\s]+", re.UNICODE)


@dataclass(frozen=True, slots=True)
class LexicalCandidate:
    verse_id: int
    chapter: int
    verse: int
    citation_key: str
    translation: str
    retrieval_score: float
    matched_by: tuple[str, ...]


def _strip_query(raw: str) -> str:
    return raw.strip()


def tokenize_query(raw: str) -> list[str]:
    """Whitespace-delimited tokens; empty / whitespace-only → []."""
    s = _strip_query(raw)
    if not s:
        return []
    return [t for t in _TOKEN_RE.findall(s) if t]


def fts_escape_token(token: str) -> str:
    """
    FTS5 token for use inside column filters (``col : <token>``).

    Hyphens, apostrophes, and most punctuation are **not** safe bare: FTS5 treats ``-``
    as NOT, so e.g. ``non-attachment`` is parsed as ``non NOT attachment`` (bogus column).
    Only letters (any script), digits, and ASCII underscore may appear unquoted.
    """
    if not token:
        return ""
    for c in token:
        if c == "_":
            continue
        if unicodedata.category(c)[0] in ("L", "N"):
            continue
        return '"' + token.replace('"', '""') + '"'
    return token


def build_lexical_match_query(tokens: list[str]) -> str:
    """
    Build MATCH expression that ORs tokens across translation, transliteration,
    theme_tags, and situation_tags only.
    """
    if not tokens:
        return ""
    parts: list[str] = []
    for tok in tokens:
        et = fts_escape_token(tok)
        if not et:
            continue
        inner = " OR ".join(f"{col} : {et}" for col in _LEXICAL_COLUMNS)
        parts.append(f"({inner})")
    if not parts:
        return ""
    # Across tokens: a row matches if any token hits any allowed column (OR semantics).
    return " OR ".join(parts)


def _bm25_to_retrieval_score(bm25: float) -> float:
    """BM25 returns smaller for better matches; invert so larger retrieval_score is better."""
    return float(-bm25)


def _column_matches_row(
    conn: sqlite3.Connection,
    *,
    rowid: int,
    column: str,
    tokens: list[str],
) -> bool:
    if not tokens or column not in _LEXICAL_COLUMNS:
        return False
    or_clause = " OR ".join(f"{column} : {fts_escape_token(t)}" for t in tokens if fts_escape_token(t))
    if not or_clause:
        return False
    match_expr = f"({or_clause})"
    row = conn.execute(
        """
        SELECT 1 AS ok
        FROM verses_fts
        WHERE verses_fts.rowid = ? AND verses_fts MATCH ?
        LIMIT 1
        """,
        (rowid, match_expr),
    ).fetchone()
    return row is not None


def matched_columns_for_row(
    conn: sqlite3.Connection,
    *,
    rowid: int,
    tokens: list[str],
) -> tuple[str, ...]:
    """Which lexical columns had an FTS hit for these tokens (post-hoc, testable)."""
    if not tokens:
        return ()
    hits = [c for c in _LEXICAL_COLUMNS if _column_matches_row(conn, rowid=rowid, column=c, tokens=tokens)]
    return tuple(hits)


def lexical_search(
    conn: sqlite3.Connection,
    query: str,
    *,
    limit: int,
) -> list[LexicalCandidate]:
    """
    Return BM25-ranked candidates. Empty or whitespace query → [].
    """
    tokens = tokenize_query(query)
    if not tokens:
        return []
    match_expr = build_lexical_match_query(tokens)
    if not match_expr:
        return []

    # FTS5 MATCH / bm25() must use the virtual table name, not an alias (see SQLite forum:
    # "FTS5: join as doesn't interoperate with tablename MATCH").
    sql = """
        SELECT
            v.id AS verse_id,
            v.chapter AS chapter,
            v.verse AS verse,
            v.citation_key AS citation_key,
            v.translation AS translation,
            bm25(verses_fts) AS bm25
        FROM verses_fts
        JOIN verses v ON v.id = verses_fts.rowid
        WHERE verses_fts MATCH ?
        ORDER BY bm25(verses_fts)
        LIMIT ?
    """
    rows = conn.execute(sql, (match_expr, limit)).fetchall()
    out: list[LexicalCandidate] = []
    for r in rows:
        rid = int(r["verse_id"])
        mb = matched_columns_for_row(conn, rowid=rid, tokens=tokens)
        out.append(
            LexicalCandidate(
                verse_id=rid,
                chapter=int(r["chapter"]),
                verse=int(r["verse"]),
                citation_key=str(r["citation_key"]),
                translation=str(r["translation"]),
                retrieval_score=_bm25_to_retrieval_score(float(r["bm25"])),
                matched_by=mb,
            )
        )
    return out
