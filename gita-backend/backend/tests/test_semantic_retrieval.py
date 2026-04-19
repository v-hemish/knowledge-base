from __future__ import annotations

import numpy as np
import pytest

from app.core.config import get_settings
from app.db.database import connect, init_schema
from app.db.ingestion import ingest_verse_inputs
from app.db.session import make_engine, make_session_factory, session_scope
from app.models.verse import Verse
from app.retrieval.cosine_reranker import order_verses_by_cosine
from app.retrieval.embedding_artifact import save_artifact
from app.retrieval.embedding_store import VerseEmbeddingIndex, load_embedding_index, set_embedding_index
from app.retrieval.pipeline import retrieve_verses_for_query
from app.schemas.verse_document import VerseInput


def test_order_verses_by_cosine_prefers_higher_similarity() -> None:
    v1 = Verse.from_row(
        {
            "id": 101,
            "chapter": 1,
            "verse": 1,
            "citation_key": "1.1",
            "translation": "a",
            "sanskrit": None,
            "transliteration": None,
            "theme_tags": "[]",
            "situation_tags": "[]",
            "use_with_care_tags": "[]",
            "translation_source": None,
        }
    )
    v2 = Verse.from_row(
        {
            "id": 102,
            "chapter": 1,
            "verse": 2,
            "citation_key": "1.2",
            "translation": "b",
            "sanskrit": None,
            "transliteration": None,
            "theme_tags": "[]",
            "situation_tags": "[]",
            "use_with_care_tags": "[]",
            "translation_source": None,
        }
    )
    emb = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    idx = VerseEmbeddingIndex(
        verse_ids=np.array([101, 102], dtype=np.int64),
        embeddings=emb,
        model_name="BAAI/bge-small-en-v1.5",
    )
    q = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    ordered = order_verses_by_cosine(q, [v1, v2], idx)
    assert ordered[0].id == 102
    assert ordered[1].id == 101

    # Intent boost tips order when cosine similarities are nearly equal.
    s = float(1.0 / np.sqrt(2.0))
    qflat = np.array([s, s, 0.0], dtype=np.float32)
    boosts = np.array([10.0, 0.0], dtype=np.float32)
    tied = order_verses_by_cosine(qflat, [v1, v2], idx, intent_boosts=boosts, intent_lambda=0.5)
    assert tied[0].id == 101
    assert tied[1].id == 102


@pytest.mark.asyncio
async def test_retrieval_pipeline_semantic_reranks_and_caps_at_three(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_path = tmp_path / "g.db"
    npz_path = data_dir / "verses_embeddings.npz"

    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("EMBEDDINGS_ARTIFACT_PATH", str(npz_path))
    monkeypatch.setenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "true")
    monkeypatch.setenv("FTS_CANDIDATE_LIMIT", "10")
    monkeypatch.setenv("FINAL_VERSE_COUNT", "3")
    get_settings.cache_clear()

    settings = get_settings()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    verses_in = [
        VerseInput(
            chapter=1,
            verse=1,
            citation_key="1.1",
            translation="sharedtoken chapter one",
            sanskrit=None,
            transliteration=None,
            theme_tags=[],
            situation_tags=[],
            use_with_care_tags=[],
        ),
        VerseInput(
            chapter=2,
            verse=2,
            citation_key="2.2",
            translation="sharedtoken chapter two",
            sanskrit=None,
            transliteration=None,
            theme_tags=[],
            situation_tags=[],
            use_with_care_tags=[],
        ),
        VerseInput(
            chapter=3,
            verse=3,
            citation_key="3.3",
            translation="sharedtoken chapter three",
            sanskrit=None,
            transliteration=None,
            theme_tags=[],
            situation_tags=[],
            use_with_care_tags=[],
        ),
    ]
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(session, verses_in)

    conn = connect(db_path)
    rows = conn.execute("SELECT id FROM verses ORDER BY id").fetchall()
    vids = [int(r[0]) for r in rows]
    conn.close()
    assert len(vids) == 3

    d = 8
    emb = np.zeros((3, d), dtype=np.float32)
    for i in range(3):
        emb[i, i] = 1.0
    save_artifact(
        npz_path,
        verse_ids=np.array(vids, dtype=np.int64),
        embeddings=emb,
        model_name="BAAI/bge-small-en-v1.5",
        normalized=True,
    )
    load_embedding_index(get_settings())

    qvec = np.zeros(d, dtype=np.float32)
    qvec[2] = 1.0

    monkeypatch.setattr(
        "app.retrieval.cosine_reranker.encode_query_vector",
        lambda model_name, query: qvec,
    )

    conn = connect(db_path)
    out = await retrieve_verses_for_query(conn, query="sharedtoken", settings=get_settings())
    conn.close()

    assert len(out) == 3
    assert out[0].citation_key == "3.3"
    assert all(v.citation_key for v in out)
    assert {v.citation_key for v in out} == {"1.1", "2.2", "3.3"}


@pytest.mark.asyncio
async def test_retrieval_pipeline_falls_back_when_embeddings_missing(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    make_verse_input,
) -> None:
    db_path = tmp_path / "onlylex.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "d"))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "true")
    get_settings.cache_clear()

    settings = get_settings()
    init_schema(connect(db_path))
    engine = make_engine(db_path)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(
            session,
            [
                make_verse_input(translation="alpha sharedlextoken"),
                make_verse_input(
                    chapter=3,
                    verse=3,
                    citation_key="3.3",
                    translation="beta sharedlextoken",
                ),
            ],
        )

    set_embedding_index(None)
    conn = connect(db_path)
    out = await retrieve_verses_for_query(conn, query="sharedlextoken", settings=settings)
    conn.close()
    assert len(out) >= 1
    assert all(v.citation for v in out)
