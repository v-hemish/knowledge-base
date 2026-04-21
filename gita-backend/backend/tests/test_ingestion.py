import asyncio
import json
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.db.database import connect, init_schema
from app.db.ingestion import ingest_verse_inputs
from app.db.session import make_engine, make_session_factory, session_scope
from app.retrieval.lexical import lexical_search
from app.retrieval.pipeline import retrieve_verses_for_query
from app.schemas.verse_document import VerseInput, parse_canonical_verse_file_payload


def test_shipped_gita_io_corpus_validates() -> None:
    """Regression: committed full-corpus JSON must match VerseInput / load_verses schema."""
    path = Path(__file__).resolve().parents[1] / "data" / "canonical_bhagavadgita_gita_io.json"
    assert path.is_file(), f"missing shipped corpus at {path}"
    raw = json.loads(path.read_text(encoding="utf-8"))
    doc = parse_canonical_verse_file_payload(raw)
    assert len(doc.verses) == 701
    assert doc.verses[0].citation_key == "1.1"
    assert doc.verses[-1].citation_key == "18.78"


def _ingest(db_path, verses: list[VerseInput]) -> None:
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        ingest_verse_inputs(session, verses)


def test_ingestion_idempotent_row_count(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "ingest.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    get_settings.cache_clear()

    verses = [
        VerseInput(
            chapter=2,
            verse=47,
            citation_key="2.47",
            translation="alpha767token",
            sanskrit=None,
            transliteration=None,
            theme_tags=["karma"],
            situation_tags=[],
            use_with_care_tags=[],
        )
    ]

    _ingest(db, verses)
    _ingest(db, verses)

    conn = connect(db)
    n = int(conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0])
    conn.close()
    assert n == 1


def test_fts_populated_after_ingest(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "fts.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()

    verses = [
        VerseInput(
            chapter=2,
            verse=47,
            citation_key="2.47",
            translation="alpha767token in translation",
            sanskrit=None,
            transliteration=None,
            theme_tags=["karma_yoga"],
            situation_tags=["battlefield"],
            use_with_care_tags=[],
        )
    ]
    _ingest(db, verses)

    conn = connect(db)
    ids_theme = [h.verse_id for h in lexical_search(conn, "karma_yoga", limit=10)]
    ids_text = [h.verse_id for h in lexical_search(conn, "alpha767token", limit=10)]
    conn.close()

    assert ids_theme
    assert ids_text
    assert ids_theme == ids_text

    settings = get_settings()
    conn = connect(db)
    hits = asyncio.run(
        retrieve_verses_for_query(conn, query="alpha767token", settings=settings),
    )
    conn.close()
    assert len(hits) == 1
    assert hits[0].citation_key == "2.47"
