import pytest

from app.core.config import get_settings
from app.db.database import connect, init_schema
from app.db.ingestion import ingest_verse_inputs
from app.db.session import make_engine, make_session_factory, session_scope
from app.retrieval.pipeline import retrieve_verses_for_query


@pytest.mark.asyncio
async def test_retrieval_fts_hit(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    make_verse_input,
) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()

    settings = get_settings()
    db_path = settings.resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(
            session,
            [
                make_verse_input(),
                make_verse_input(
                    chapter=6,
                    verse=5,
                    citation_key="6.5",
                    translation="other verse without marker",
                ),
            ],
        )

    conn = connect(db_path)
    verses = await retrieve_verses_for_query(conn, query="distincttoken", settings=settings)
    assert len(verses) == 1
    assert verses[0].chapter == 2
    assert verses[0].verse == 47
    conn.close()
