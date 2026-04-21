"""
Idempotent seeding script for local development (canonical JSON → SQLite).

FUTURE: ingest pipeline from TEI/CSV with checksums and provenance columns.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(_backend_root()))

    from app.core.config import Settings
    from app.db.database import connect, init_schema
    from app.db.ingestion import ingest_verse_inputs
    from app.db.session import make_engine, make_session_factory, session_scope
    from app.schemas.daily_practice_seed import verse_inputs_from_daily_practice_spec
    from app.schemas.verse_document import VerseInput, parse_canonical_verse_file_payload

    settings = Settings()
    db_path = settings.resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)

    root = _backend_root()
    data_dir = root / "data"
    env_path = (os.environ.get("GITA_SEED_JSON") or "").strip()

    corpus_path: Path | None = None

    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = root / p
        corpus_path = p if p.is_file() else None
        if corpus_path is None:
            print(f"seed_database: GITA_SEED_JSON not found: {p}", file=sys.stderr)
            return 2
    else:
        daily = data_dir / "gita_daily_practice_app_spec_with_sanskrit.json"
        full_corpus = data_dir / "canonical_bhagavadgita_gita_io.json"
        sample = data_dir / "canonical_sample.json"
        if daily.is_file():
            corpus_path = daily
        elif full_corpus.is_file():
            corpus_path = full_corpus
        elif sample.is_file():
            corpus_path = sample

    if corpus_path is None or not corpus_path.is_file():
        print(
            "seed_database: missing corpus (set GITA_SEED_JSON or add one of:\n"
            f"  {data_dir / 'gita_daily_practice_app_spec_with_sanskrit.json'}\n"
            f"  {data_dir / 'canonical_bhagavadgita_gita_io.json'}\n"
            f"  {data_dir / 'canonical_sample.json'})",
            file=sys.stderr,
        )
        return 2

    try:
        raw = json.loads(corpus_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"seed_database: cannot read corpus JSON: {e}", file=sys.stderr)
        return 2

    use_daily_pack = isinstance(raw, dict) and isinstance(raw.get("starter_verse_pack"), list)
    if use_daily_pack:
        verses: list[VerseInput] = verse_inputs_from_daily_practice_spec(raw)
        doc_label = f"{corpus_path.name} (starter_verse_pack)"
    else:
        doc = parse_canonical_verse_file_payload(raw)
        verses = doc.verses
        doc_label = corpus_path.name

    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        n = ingest_verse_inputs(session, verses)

    if n <= 0:
        print(
            "seed_database: ingest wrote 0 verses (check JSON schema and DB permissions).",
            file=sys.stderr,
        )
        return 3

    conn = connect(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) AS c FROM verses").fetchone()
        total = int(row["c"]) if row is not None else 0
    finally:
        conn.close()

    print(f"Seeded {n} verse(s) from {doc_label} into {db_path}")
    print(f"Verses table row count (after run): {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
