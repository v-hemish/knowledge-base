import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import connect, init_schema
from app.db.ingestion import ingest_verse_inputs
from app.db.session import make_engine, make_session_factory, session_scope
from app.main import create_app
from app.schemas.verse_document import VerseInput


def test_retrieve_returns_exact_db_translation_and_citation(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "r.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()

    unique_t = "UNIQUE_DB_TRANSLATION_XYZ"
    init_schema(connect(db))
    engine = make_engine(db)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(
            session,
            [
                VerseInput(
                    chapter=2,
                    verse=47,
                    citation_key="2.47",
                    translation=f"alpha {unique_t} beta",
                    sanskrit="sa-db",
                    transliteration="tr-db",
                    theme_tags=[],
                    situation_tags=[],
                    use_with_care_tags=[],
                ),
            ],
        )

    client = TestClient(create_app())
    resp = client.post("/api/v1/guidance/retrieve", json={"query": unique_t})
    assert resp.status_code == 200
    body = resp.json()
    assert body["explanation_status"] == "verses_only"
    assert len(body["selected_verses"]) == 1
    card = body["selected_verses"][0]
    assert card["translation"] == f"alpha {unique_t} beta"
    assert card["citation_key"] == "2.47"
    assert card["chapter"] == 2
    assert card["verse"] == 47
    assert card["sanskrit"] == "sa-db"
    assert card["transliteration"] == "tr-db"
    assert "stage-1 rank" in card["why_selected_short"]
    assert body["reflection_prompt"]


def test_retrieve_caps_at_three_verses(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "many.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    monkeypatch.setenv("FTS_CANDIDATE_LIMIT", "24")
    monkeypatch.setenv("FINAL_VERSE_COUNT", "3")
    get_settings.cache_clear()

    tok = "manytokencap"
    init_schema(connect(db))
    engine = make_engine(db)
    verses = [
        VerseInput(
            chapter=c,
            verse=c,
            citation_key=f"{c}.{c}",
            translation=f"verse {c} {tok}",
            sanskrit=None,
            transliteration=None,
            theme_tags=[],
            situation_tags=[],
            use_with_care_tags=[],
        )
        for c in range(1, 6)
    ]
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, verses)

    client = TestClient(create_app())
    resp = client.post("/api/v1/guidance/retrieve", json={"query": tok})
    assert resp.status_code == 200
    body = resp.json()
    assert 1 <= len(body["selected_verses"]) <= 3


def test_retrieve_rejects_blank_query() -> None:
    client = TestClient(create_app())
    resp = client.post("/api/v1/guidance/retrieve", json={"query": "  \t"})
    assert resp.status_code == 422


def test_retrieve_no_hits(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "empty.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()
    init_schema(connect(db))

    client = TestClient(create_app())
    resp = client.post("/api/v1/guidance/retrieve", json={"query": "zzzznonexistenttoken"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["selected_verses"] == []
    assert body["explanation_status"] == "no_hits"
    assert body["reflection_prompt"] is None
