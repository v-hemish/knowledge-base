from pathlib import Path

import numpy as np
import pytest

from app.core.config import Settings, get_settings
from app.retrieval.embedding_artifact import load_artifact, meta_path_for_npz, save_artifact
from app.retrieval.embedding_store import load_embedding_index, set_embedding_index


def test_embedding_artifact_roundtrip(tmp_path: Path) -> None:
    npz = tmp_path / "e.npz"
    ids = np.array([10, 20, 30], dtype=np.int64)
    emb = np.array([[1.0, 0.0], [0.0, 1.0], [0.6, 0.8]], dtype=np.float32)
    save_artifact(npz, verse_ids=ids, embeddings=emb, model_name="test-model", normalized=True)
    assert meta_path_for_npz(npz).is_file()
    ids2, emb2, meta = load_artifact(npz)
    assert np.array_equal(ids2, ids)
    assert emb2.shape == emb.shape
    assert meta.model_name == "test-model"
    assert meta.embedding_dim == 2


def test_embedding_index_loads_from_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    npz = tmp_path / "verses_embeddings.npz"
    ids = np.array([1], dtype=np.int64)
    emb = np.ones((1, 4), dtype=np.float32)
    save_artifact(npz, verse_ids=ids, embeddings=emb, model_name="BAAI/bge-small-en-v1.5", normalized=True)

    monkeypatch.setenv("EMBEDDINGS_ARTIFACT_PATH", str(npz))
    monkeypatch.setenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    get_settings.cache_clear()

    idx = load_embedding_index(get_settings())
    assert idx is not None
    assert idx.embedding_dim == 4
    assert idx.has_all([1])
    set_embedding_index(None)
    get_settings.cache_clear()


def test_empty_embeddings_artifact_env_is_unset(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Blank .env lines must not resolve to Path('') (which breaks embed_verses output path)."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("EMBEDDINGS_ARTIFACT_PATH", "")
    s = Settings()
    assert s.embeddings_artifact_path is None
    assert s.resolved_embeddings_npz_path() == (tmp_path / "verses_embeddings.npz").resolve()
