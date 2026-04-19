"""
On-disk verse embedding bundle (no vector DB).

Layout:
  - `verses_embeddings.npz` — compressed arrays `verse_ids` (int64), `embeddings` (float32, N×D)
  - `verses_embeddings.meta.json` — model name, dim, version (next to the .npz)

FUTURE: mmap large matrices, shard by chapter, checksum verification.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ARTIFACT_VERSION = 1


@dataclass(frozen=True, slots=True)
class EmbeddingArtifactMeta:
    artifact_version: int
    model_name: str
    embedding_dim: int
    num_verses: int
    normalized: bool

    def to_json(self) -> str:
        return json.dumps(
            {
                "artifact_version": self.artifact_version,
                "model_name": self.model_name,
                "embedding_dim": self.embedding_dim,
                "num_verses": self.num_verses,
                "normalized": self.normalized,
            },
            indent=2,
        )

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> EmbeddingArtifactMeta:
        return cls(
            artifact_version=int(d["artifact_version"]),
            model_name=str(d["model_name"]),
            embedding_dim=int(d["embedding_dim"]),
            num_verses=int(d["num_verses"]),
            normalized=bool(d.get("normalized", True)),
        )


def meta_path_for_npz(npz_path: Path) -> Path:
    return npz_path.with_suffix(".meta.json")


def save_artifact(
    npz_path: Path,
    *,
    verse_ids: np.ndarray,
    embeddings: np.ndarray,
    model_name: str,
    normalized: bool = True,
) -> None:
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    ids = np.asarray(verse_ids, dtype=np.int64)
    emb = np.asarray(embeddings, dtype=np.float32)
    if ids.ndim != 1:
        raise ValueError("verse_ids must be 1-D")
    if emb.ndim != 2 or emb.shape[0] != ids.shape[0]:
        raise ValueError("embeddings must be (N, D) aligned with verse_ids")
    meta = EmbeddingArtifactMeta(
        artifact_version=ARTIFACT_VERSION,
        model_name=model_name,
        embedding_dim=int(emb.shape[1]),
        num_verses=int(emb.shape[0]),
        normalized=normalized,
    )
    np.savez_compressed(npz_path, verse_ids=ids, embeddings=emb)
    meta_path_for_npz(npz_path).write_text(meta.to_json(), encoding="utf-8")


def load_artifact(npz_path: Path) -> tuple[np.ndarray, np.ndarray, EmbeddingArtifactMeta]:
    if not npz_path.is_file():
        raise FileNotFoundError(str(npz_path))
    mp = meta_path_for_npz(npz_path)
    if not mp.is_file():
        raise FileNotFoundError(str(mp))
    meta = EmbeddingArtifactMeta.from_dict(json.loads(mp.read_text(encoding="utf-8")))
    data = np.load(npz_path, allow_pickle=False)
    try:
        ids = np.asarray(data["verse_ids"], dtype=np.int64).reshape(-1)
        emb = np.asarray(data["embeddings"], dtype=np.float32)
    finally:
        data.close()
    if emb.shape[0] != ids.shape[0]:
        raise ValueError("verse_ids length does not match embeddings rows")
    if emb.shape[1] != meta.embedding_dim:
        raise ValueError("embedding_dim meta does not match matrix")
    if meta.num_verses != int(ids.shape[0]):
        raise ValueError("num_verses meta does not match matrix")
    return ids, emb, meta
