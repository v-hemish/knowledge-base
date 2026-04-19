"""
Idempotent seeding script for local development (canonical JSON → SQLite).

FUTURE: ingest pipeline from TEI/CSV with checksums and provenance columns.
"""

from __future__ import annotations

import json
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
    from app.schemas.verse_document import parse_canonical_verse_file_payload

    settings = Settings()
    db_path = settings.resolved_database_path()
    init_schema(connect(db_path))
    engine = make_engine(db_path)

    sample = _backend_root() / "data" / "canonical_sample.json"
    raw = json.loads(sample.read_text(encoding="utf-8"))
    doc = parse_canonical_verse_file_payload(raw)

    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        n = ingest_verse_inputs(session, doc.verses)

    print(f"Seeded {n} verses into {settings.resolved_database_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
