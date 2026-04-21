from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import connect, init_schema
from app.db.ingestion import ingest_verse_inputs
from app.db.session import make_engine, make_session_factory, session_scope
from app.main import create_app
from app.schemas.verse_document import VerseInput


def test_get_verse_by_key_returns_sanskrit(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "vdl.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()

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
                    sanskrit="देव",
                    transliteration="deva",
                    translation="A long enough translation string for the row.",
                    theme_tags=[],
                    situation_tags=[],
                    use_with_care_tags=[],
                ),
            ],
        )

    client = TestClient(create_app())
    r = client.get("/api/v1/verses/by-key/2.47")
    assert r.status_code == 200
    body = r.json()
    assert body["citation_key"] == "2.47"
    assert body["sanskrit"] == "देव"
    assert body["transliteration"] == "deva"
    assert "why_selected_short" in body


def test_post_verses_by_keys_batch(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "vdl2.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()

    init_schema(connect(db))
    engine = make_engine(db)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(
            session,
            [
                VerseInput(
                    chapter=2,
                    verse=13,
                    citation_key="2.13",
                    sanskrit=None,
                    transliteration=None,
                    translation="Another long enough translation for verse two thirteen.",
                    theme_tags=[],
                    situation_tags=[],
                    use_with_care_tags=[],
                ),
                VerseInput(
                    chapter=2,
                    verse=14,
                    citation_key="2.14",
                    sanskrit=None,
                    transliteration=None,
                    translation="Yet another long enough translation for verse two fourteen.",
                    theme_tags=[],
                    situation_tags=[],
                    use_with_care_tags=[],
                ),
            ],
        )

    client = TestClient(create_app())
    r = client.post(
        "/api/v1/verses/by-keys",
        json={"citation_keys": ["2.14", "2.13", "9.99"]},
    )
    assert r.status_code == 200
    verses = r.json()["verses"]
    assert set(verses.keys()) == {"2.14", "2.13"}
    assert verses["2.13"]["citation_key"] == "2.13"


def test_citation_index_ordered_and_omits_placeholders(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "vdl4.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    get_settings.cache_clear()

    init_schema(connect(db))
    engine = make_engine(db)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(
            session,
            [
                VerseInput(
                    chapter=2,
                    verse=14,
                    citation_key="2.14",
                    translation="Short",
                    theme_tags=[],
                    situation_tags=[],
                    use_with_care_tags=[],
                ),
                VerseInput(
                    chapter=2,
                    verse=47,
                    citation_key="2.47",
                    translation="A long enough translation for verse two forty-seven here.",
                    theme_tags=[],
                    situation_tags=[],
                    use_with_care_tags=[],
                ),
            ],
        )

    client = TestClient(create_app())
    r = client.get("/api/v1/verses/citation-index")
    assert r.status_code == 200
    keys = r.json()["citation_keys"]
    assert keys == ["2.47"]


def test_get_verse_by_key_404(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "vdl3.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    get_settings.cache_clear()
    init_schema(connect(db))

    client = TestClient(create_app())
    assert client.get("/api/v1/verses/by-key/1.1").status_code == 404
