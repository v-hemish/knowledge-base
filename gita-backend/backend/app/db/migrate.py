"""
Lightweight schema upgrades without Alembic.

FUTURE: migrate to Alembic when multiple environments need reversible history.
"""

from __future__ import annotations

import sqlite3

from app.db.ddl import CREATE_FTS_ONLY_SQL, DROP_FTS_SQL, SCHEMA_VERSION


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(r[1]) for r in rows}


def _verses_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='verses' LIMIT 1"
    ).fetchone()
    return row is not None


def _ensure_verse_columns(conn: sqlite3.Connection) -> None:
    if not _verses_table_exists(conn):
        return
    cols = _table_columns(conn, "verses")
    if "citation_key" not in cols:
        conn.execute("ALTER TABLE verses ADD COLUMN citation_key TEXT")
        conn.execute(
            """
            UPDATE verses
            SET citation_key = (chapter || '.' || verse)
            WHERE citation_key IS NULL OR citation_key = ''
            """
        )
    if "theme_tags" not in cols:
        conn.execute(
            "ALTER TABLE verses ADD COLUMN theme_tags TEXT NOT NULL DEFAULT '[]'"
        )
    if "situation_tags" not in cols:
        conn.execute(
            "ALTER TABLE verses ADD COLUMN situation_tags TEXT NOT NULL DEFAULT '[]'"
        )
    if "use_with_care_tags" not in cols:
        conn.execute(
            "ALTER TABLE verses ADD COLUMN use_with_care_tags TEXT NOT NULL DEFAULT '[]'"
        )


def _recreate_fts(conn: sqlite3.Connection) -> None:
    conn.executescript(DROP_FTS_SQL)
    conn.executescript(CREATE_FTS_ONLY_SQL)
    conn.execute("INSERT INTO verses_fts(verses_fts) VALUES('rebuild')")


def apply_migrations(conn: sqlite3.Connection) -> None:
    row = conn.execute("PRAGMA user_version").fetchone()
    current = int(row[0]) if row is not None else 0
    if current >= SCHEMA_VERSION:
        return

    _ensure_verse_columns(conn)
    _recreate_fts(conn)

    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
