"""
Load canonical normalized JSON into SQLite (validate → upsert → FTS rebuild).

FUTURE: batch transactions, content hashes, and partial-file rollback.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Ingest canonical verse JSON into SQLite.")
    parser.add_argument(
        "json_path",
        type=Path,
        help="Path to canonical JSON (`{\"verses\":[...]}` or a bare array).",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="Override SQLite path (defaults to Settings.resolved_database_path()).",
    )
    args = parser.parse_args(argv)

    sys.path.insert(0, str(_backend_root()))

    from app.core.config import Settings
    from app.core.paths import resolve_existing_file
    from app.db.database import connect, init_schema
    from app.db.ingestion import ingest_verse_inputs
    from app.db.session import make_engine, make_session_factory, session_scope
    from app.schemas.verse_document import parse_canonical_verse_file_payload

    root = _backend_root().resolve()

    def _json_path() -> Path:
        raw = Path(args.json_path).expanduser()
        if raw.is_absolute():
            return raw.resolve()
        p = (root / raw).resolve()
        try:
            p.relative_to(root)
        except ValueError as exc:
            raise SystemExit(
                f"json_path must resolve under backend root ({root}), got: {p}"
            ) from exc
        return p

    json_path = resolve_existing_file(_json_path(), description="canonical JSON")

    settings = Settings()
    if args.database is None:
        db_path = settings.resolved_database_path()
    else:
        raw_db = Path(args.database).expanduser()
        if raw_db.is_absolute():
            db_path = raw_db.resolve()
        else:
            db_path = (root / raw_db).resolve()
            try:
                db_path.relative_to(root)
            except ValueError as exc:
                raise SystemExit(
                    f"--database must resolve under backend root ({root}), got: {db_path}"
                ) from exc
    init_schema(connect(db_path))
    engine = make_engine(db_path)

    raw = json.loads(json_path.read_text(encoding="utf-8"))
    doc = parse_canonical_verse_file_payload(raw)

    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        n = ingest_verse_inputs(session, doc.verses)

    print(f"Ingested {n} verses into {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
