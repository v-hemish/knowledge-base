"""
Validate canonical JSON and upsert verses; keep FTS in sync.

FUTURE: content-addressed snapshots, checksum per file, dry-run diff reporting.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db.orm import VerseRow
from app.schemas.verse_document import VerseInput

_log = logging.getLogger(__name__)


def _tags_json(tags: Sequence[str]) -> str:
    """Stable JSON text for idempotent on-disk comparisons."""
    return json.dumps(list(tags), ensure_ascii=False, sort_keys=False)


def ingest_verse_inputs(session: Session, verses: Sequence[VerseInput]) -> int:
    """
    Upsert by (chapter, verse). Commits are the caller's responsibility (session_scope).
    Refreshes FTS via external-content `rebuild` (idempotent, safe after bulk upserts).
    """
    count = 0
    for v in verses:
        values = {
            "chapter": v.chapter,
            "verse": v.verse,
            "citation_key": v.citation_key,
            "sanskrit": v.sanskrit,
            "transliteration": v.transliteration,
            "translation": v.translation,
            "theme_tags": _tags_json(v.theme_tags),
            "situation_tags": _tags_json(v.situation_tags),
            "use_with_care_tags": _tags_json(v.use_with_care_tags),
            "translation_source": v.translation_source,
        }
        insert_stmt = sqlite_insert(VerseRow).values(**values)
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["chapter", "verse"],
            set_={
                "citation_key": insert_stmt.excluded.citation_key,
                "sanskrit": insert_stmt.excluded.sanskrit,
                "transliteration": insert_stmt.excluded.transliteration,
                "translation": insert_stmt.excluded.translation,
                "theme_tags": insert_stmt.excluded.theme_tags,
                "situation_tags": insert_stmt.excluded.situation_tags,
                "use_with_care_tags": insert_stmt.excluded.use_with_care_tags,
                "translation_source": insert_stmt.excluded.translation_source,
            },
        )
        session.execute(upsert_stmt)
        count += 1

    session.execute(text("INSERT INTO verses_fts(verses_fts) VALUES('rebuild')"))
    _log.info("ingestion_complete", extra={"upserted": count})
    return count
