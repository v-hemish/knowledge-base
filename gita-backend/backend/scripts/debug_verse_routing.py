#!/usr/bin/env python3
"""
Print verse-routing stages for eval prompts (stdout).

For each query:
- top 3 citations after raw retrieval
- top 3 after rank + intent (before theme pins)
- top 3 after theme pins (before final verse cap)
- chosen generation verses (same logic as guidance stream)

Usage (from backend/):
  python scripts/debug_verse_routing.py
  python scripts/debug_verse_routing.py --queries data/guidance_review_queries.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

# package imports assume cwd = backend/
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _top3_keys(verses: list) -> list[str]:
    return [v.citation_key for v in verses[:3]]


async def _run_one(conn, settings, qid: str, query: str) -> None:
    from app.llm.query_intent import rank_verses_by_intent_and_fit, select_verses_for_generation
    from app.llm.theme_routing import apply_theme_ordered_pins
    from app.retrieval.pipeline import retrieve_verses_for_query

    raw = await retrieve_verses_for_query(conn, query=query, settings=settings)
    ranked_before_pins = rank_verses_by_intent_and_fit(query, raw)
    pinned = apply_theme_ordered_pins(query, ranked_before_pins)
    capped = pinned[: settings.final_verse_count]
    gen_default = select_verses_for_generation(query, capped, max_verses=1)
    gen_two = select_verses_for_generation(query, capped, max_verses=2)

    print(f"--- {qid} ---")
    print(f"query: {query[:120]}{'…' if len(query) > 120 else ''}")
    print(f"  top3 raw retrieve:          {_top3_keys(raw)}")
    print(f"  top3 after rank (pre-pin): {_top3_keys(ranked_before_pins)}")
    print(f"  top3 after theme pins:      {_top3_keys(pinned)}")
    print(f"  top3 after final cap:       {_top3_keys(capped)}")
    print(f"  generation (max=1):         {[v.citation_key for v in gen_default]}")
    print(f"  generation (max=2):         {[v.citation_key for v in gen_two]}")
    print()


async def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--queries",
        type=Path,
        default=_ROOT / "data" / "guidance_review_queries.json",
        help="JSON with items[{id,query}]",
    )
    args = p.parse_args()
    load_dotenv(_ROOT / ".env")

    from app.core.config import get_settings
    from app.db.database import connect

    get_settings.cache_clear()
    settings = get_settings()
    path = args.queries if args.queries.is_absolute() else _ROOT / args.queries
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") or []
    if not items:
        print("No items.", file=sys.stderr)
        return 2

    dbp = settings.resolved_database_path()
    conn = connect(dbp)
    try:
        for it in items:
            await _run_one(conn, settings, str(it.get("id", "")), str(it.get("query", "")))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
