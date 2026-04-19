"""
Run retrieval eval suite and print a CLI summary.

Usage (from `backend/`):
  python scripts/run_eval.py
  python scripts/run_eval.py --suite tests/fixtures/eval_cases.json --database /path/to/gita.db

FUTURE: export JSON lines for dashboards; pair with explanation human grades.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Run retrieval eval suite.")
    parser.add_argument(
        "--suite",
        type=Path,
        default=None,
        help="Path to eval_cases.json (default: tests/fixtures/eval_cases.json under backend root).",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="SQLite DB path (defaults to Settings.resolved_database_path()).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="How many retrieved citations to score per case.",
    )
    args = parser.parse_args(argv)

    sys.path.insert(0, str(_backend_root()))

    from app.core.config import Settings
    from app.core.paths import resolve_existing_file
    from app.db.database import connect
    from app.evals.runner import format_cli_summary, load_suite, run_suite

    root = _backend_root().resolve()

    def _suite_path() -> Path:
        if args.suite is None:
            return (root / "tests" / "fixtures" / "eval_cases.json").resolve()
        raw = args.suite.expanduser()
        if raw.is_absolute():
            p = raw.resolve()
        else:
            p = (root / raw).resolve()
            try:
                p.relative_to(root)
            except ValueError as exc:
                raise SystemExit(
                    f"--suite must resolve under backend root ({root}), got: {p}"
                ) from exc
        return p

    suite_path = resolve_existing_file(_suite_path(), description="eval suite")

    settings = Settings()
    if args.database is None:
        db_path = settings.resolved_database_path()
    else:
        raw_db = args.database.expanduser()
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

    suite = load_suite(suite_path)
    conn = connect(db_path)

    async def _run() -> None:
        results, metrics = await run_suite(conn, suite=suite, settings=settings, top_k=args.top_k)
        print(format_cli_summary(suite, metrics, results))

    try:
        asyncio.run(_run())
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
