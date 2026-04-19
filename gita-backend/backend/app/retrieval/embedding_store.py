"""In-memory verse embedding matrix loaded at startup from local artifacts."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import numpy as np

from app.core.config import Settings
from app.retrieval.embedding_artifact import load_artifact

_log = logging.getLogger(__name__)

_index: "VerseEmbeddingIndex | None" = None
_load_lock = threading.Lock()


class VerseEmbeddingIndex:
    """Maps verse row ids to precomputed L2-normalized embedding rows."""

    __slots__ = ("verse_ids", "embeddings", "id_to_row", "model_name", "embedding_dim")

    def __init__(
        self,
        *,
        verse_ids: np.ndarray,
        embeddings: np.ndarray,
        model_name: str,
    ) -> None:
        self.verse_ids = verse_ids
        self.embeddings = embeddings.astype(np.float32, copy=False)
        self.model_name = model_name
        self.embedding_dim = int(embeddings.shape[1])
        self.id_to_row: dict[int, int] = {int(vid): i for i, vid in enumerate(verse_ids.tolist())}

    @classmethod
    def from_npz(cls, npz_path: Path) -> VerseEmbeddingIndex:
        ids, emb, meta = load_artifact(npz_path)
        return cls(verse_ids=ids, embeddings=emb, model_name=meta.model_name)

    def has_all(self, verse_ids: list[int]) -> bool:
        return all(vid in self.id_to_row for vid in verse_ids)

    def row_matrix_for(self, verse_ids: list[int]) -> np.ndarray:
        """Stack embedding rows in the same order as `verse_ids` (float32, N×D)."""
        idxs = [self.id_to_row[vid] for vid in verse_ids]
        return self.embeddings[idxs].astype(np.float32, copy=False)


def get_embedding_index() -> VerseEmbeddingIndex | None:
    return _index


def set_embedding_index(idx: VerseEmbeddingIndex | None) -> None:
    global _index
    _index = idx


def load_embedding_index(settings: Settings) -> VerseEmbeddingIndex | None:
    """Load from disk; returns None if missing or invalid (caller falls back to lexical-only)."""
    path = settings.resolved_embeddings_npz_path()
    if not path.is_file():
        _log.warning("embedding_artifact_missing", extra={"path": str(path)})
        with _load_lock:
            set_embedding_index(None)
        return None
    with _load_lock:
        if not path.is_file():
            set_embedding_index(None)
            return None
        try:
            idx = VerseEmbeddingIndex.from_npz(path)
        except Exception as exc:
            _log.warning(
                "embedding_artifact_load_failed",
                extra={"path": str(path), "error": str(exc)},
            )
            set_embedding_index(None)
            return None
        set_embedding_index(idx)
        _log.info(
            "embedding_artifact_loaded",
            extra={"path": str(path), "rows": int(idx.verse_ids.shape[0]), "dim": idx.embedding_dim},
        )
        return idx
