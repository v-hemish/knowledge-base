import sqlite3

from app.models.verse import Verse


def fetch_verses_by_ids(conn: sqlite3.Connection, ids: list[int]) -> dict[int, Verse]:
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    sql = f"""
        SELECT
            id,
            chapter,
            verse,
            citation_key,
            translation,
            sanskrit,
            transliteration,
            theme_tags,
            situation_tags,
            use_with_care_tags,
            translation_source
        FROM verses
        WHERE id IN ({placeholders})
    """
    rows = conn.execute(sql, ids).fetchall()
    out: dict[int, Verse] = {}
    for r in rows:
        out[int(r["id"])] = Verse.from_row(dict(r))
    return out


def fetch_verses_by_citation_keys(
    conn: sqlite3.Connection, citation_keys: list[str]
) -> dict[str, Verse]:
    """Lookup by canonical citation_key (e.g. ``2.47``). Order is not preserved."""
    if not citation_keys:
        return {}
    placeholders = ",".join("?" * len(citation_keys))
    sql = f"""
        SELECT
            id,
            chapter,
            verse,
            citation_key,
            translation,
            sanskrit,
            transliteration,
            theme_tags,
            situation_tags,
            use_with_care_tags,
            translation_source
        FROM verses
        WHERE citation_key IN ({placeholders})
    """
    rows = conn.execute(sql, citation_keys).fetchall()
    out: dict[str, Verse] = {}
    for r in rows:
        out[str(r["citation_key"])] = Verse.from_row(dict(r))
    return out
