"""
Precompute verse embeddings (BGE-small-en-v1.5 by default) and write local artifacts.

Outputs under DATA_DIR (or next to --database):
  - verses_embeddings.npz
  - verses_embeddings.meta.json

FUTURE: incremental updates by verse checksum, multi-GPU batching.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Precompute verse embeddings for SQLite corpus.")
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="SQLite path (defaults to Settings.resolved_database_path()).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output .npz path (defaults to Settings.resolved_embeddings_npz_path()).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="sentence-transformers model id (defaults to Settings.embedding_model).",
    )
    parser.add_argument("--batch-size", type=int, default=32, help="Encode batch size.")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(_backend_root()))

    import numpy as np
    from sentence_transformers import SentenceTransformer

    from app.core.config import Settings
    from app.db.database import connect
    from app.models.verse import Verse
    from app.retrieval.embedding_artifact import save_artifact
    from app.retrieval.passage_text import passage_for_embedding

    root = _backend_root().resolve()
    settings = Settings()

    def _under_backend(p: Path | None, fallback: Path) -> Path:
        if p is None:
            return fallback
        raw = p.expanduser()
        if raw.is_absolute():
            return raw.resolve()
        q = (root / raw).resolve()
        try:
            q.relative_to(root)
        except ValueError as exc:
            raise SystemExit(
                f"Path must resolve under backend root ({root}), got: {q}"
            ) from exc
        return q

    db_path = _under_backend(args.database, settings.resolved_database_path())
    out_path = _under_backend(args.output, settings.resolved_embeddings_npz_path())
    model_name = args.model or settings.embedding_model

    conn = connect(db_path)
    rows = conn.execute(
        """
        SELECT id, chapter, verse, citation_key, translation, sanskrit, transliteration,
               theme_tags, situation_tags, use_with_care_tags, translation_source
        FROM verses
        ORDER BY id
        """
    ).fetchall()
    conn.close()
    if not rows:
        print("No verses in database; nothing to embed.")
        return 1

    verses = [Verse.from_row(dict(r)) for r in rows]
    passages = [passage_for_embedding(v) for v in verses]
    ids = np.array([v.id for v in verses], dtype=np.int64)

    print(f"Encoding {len(passages)} verses with {model_name} …")
    model = SentenceTransformer(model_name)
    emb = model.encode(
        passages,
        batch_size=max(1, args.batch_size),
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype(np.float32)

    save_artifact(out_path, verse_ids=ids, embeddings=emb, model_name=model_name, normalized=True)
    print(f"Wrote {out_path} and meta ({emb.shape[0]} × {emb.shape[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
