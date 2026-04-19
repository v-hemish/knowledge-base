import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import connect, init_schema
from app.db.ingestion import ingest_verse_inputs
from app.db.session import make_engine, make_session_factory, session_scope
from app.main import create_app
from app.retrieval.lexical import lexical_search, tokenize_query
from app.schemas.verse_document import VerseInput
from app.services.lexical_retrieval_service import LexicalRetrievalService


def _seed_db(db_path, verses: list[VerseInput]) -> None:
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, verses)


def test_lexical_empty_query_returns_no_hits(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "lex.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    get_settings.cache_clear()
    _seed_db(
        db,
        [
            VerseInput(
                chapter=2,
                verse=47,
                citation_key="2.47",
                translation="uniquewolf token in translation",
                transliteration=None,
                theme_tags=["duty"],
                situation_tags=[],
                use_with_care_tags=[],
            )
        ],
    )
    conn = connect(db)
    assert lexical_search(conn, "", limit=10) == []
    assert lexical_search(conn, "   \n\t", limit=10) == []
    assert tokenize_query("") == []
    conn.close()


def test_lexical_exact_keyword_hit(
    tmp_path, monkeypatch: pytest.MonkeyPatch, make_verse_input
) -> None:
    db = tmp_path / "lex2.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    get_settings.cache_clear()

    _seed_db(
        db,
        [
            make_verse_input(translation="plain boring text"),
            make_verse_input(
                chapter=6,
                verse=5,
                citation_key="6.5",
                translation="uniquewolf appears here only",
            ),
        ],
    )
    conn = connect(db)
    hits = lexical_search(conn, "uniquewolf", limit=10)
    conn.close()

    assert len(hits) == 1
    assert hits[0].citation_key == "6.5"
    assert isinstance(hits[0].retrieval_score, float)
    assert "translation" in hits[0].matched_by


def test_lexical_situation_tags_hit(
    tmp_path, monkeypatch: pytest.MonkeyPatch, make_verse_input
) -> None:
    db = tmp_path / "lex_sit.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    get_settings.cache_clear()

    _seed_db(
        db,
        [
            make_verse_input(translation="x", situation_tags=[]),
            make_verse_input(
                chapter=4,
                verse=4,
                citation_key="4.4",
                translation="y",
                situation_tags=["aurora_situation_marker"],
            ),
        ],
    )
    conn = connect(db)
    hits = lexical_search(conn, "aurora_situation_marker", limit=10)
    conn.close()
    assert len(hits) == 1
    assert "situation_tags" in hits[0].matched_by


def test_lexical_thematic_hit_on_theme_tags(
    tmp_path, monkeypatch: pytest.MonkeyPatch, make_verse_input
) -> None:
    db = tmp_path / "lex3.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    get_settings.cache_clear()

    _seed_db(
        db,
        [
            make_verse_input(translation="no keyword here", theme_tags=["other"]),
            make_verse_input(
                chapter=3,
                verse=3,
                citation_key="3.3",
                translation="unrelated",
                theme_tags=["zephyr_theme_marker"],
                situation_tags=[],
            ),
        ],
    )
    conn = connect(db)
    hits = lexical_search(conn, "zephyr_theme_marker", limit=10)
    conn.close()

    assert len(hits) == 1
    assert hits[0].verse_id >= 1
    assert "theme_tags" in hits[0].matched_by


def test_lexical_no_results(tmp_path, monkeypatch: pytest.MonkeyPatch, make_verse_input) -> None:
    db = tmp_path / "lex4.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    get_settings.cache_clear()

    _seed_db(db, [make_verse_input()])
    conn = connect(db)
    hits = lexical_search(conn, "zzzzabsenttoken99999", limit=10)
    conn.close()
    assert hits == []


def test_lexical_retrieval_service_delegates(
    tmp_path, monkeypatch: pytest.MonkeyPatch, make_verse_input
) -> None:
    db = tmp_path / "lex5.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("FTS_CANDIDATE_LIMIT", "5")
    get_settings.cache_clear()

    _seed_db(db, [make_verse_input(translation="servicerelay unique")])
    settings = get_settings()
    conn = connect(db)
    svc = LexicalRetrievalService()
    hits = svc.search(conn, query="servicerelay", settings=settings)
    conn.close()
    assert len(hits) == 1


def test_debug_endpoint_lexical(tmp_path, monkeypatch: pytest.MonkeyPatch, make_verse_input) -> None:
    db = tmp_path / "lex6.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    get_settings.cache_clear()

    _seed_db(db, [make_verse_input(translation="endpointtoken unique")])
    client = TestClient(create_app())
    resp = client.get("/api/v1/retrieval/lexical", params={"q": "endpointtoken"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["citation_key"] == "2.47"
    assert "verse_id" in body[0]
    assert "retrieval_score" in body[0]
    assert "translation" in body[0]["matched_by"]
