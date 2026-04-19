#!/usr/bin/env python3
"""
Score saved guidance I/O JSON (e.g. from the stream API) using heuristic checks.

Usage (from backend/):
  python scripts/score_guidance_output_eval.py
  python scripts/score_guidance_output_eval.py --input data/guidance_model_review.json

Requires PYTHONPATH=backend root (script inserts parent dir like run_eval.py).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _opening_phrase(text: str) -> str:
    t = (text or "").strip().lower()
    m = re.match(r"^([^.!?]{0,80})", t)
    return (m.group(1) if m else t[:80]).strip()


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Heuristic scores for guidance eval JSON.")
    p.add_argument(
        "--input",
        type=Path,
        default=None,
        help="JSON with {items:[{id,input,output,verses_shown,...}]} (default: data/guidance_model_review.json).",
    )
    args = p.parse_args(argv)

    sys.path.insert(0, str(_backend_root()))
    from app.llm.query_intent import analyze_query
    from app.llm.guidance_validation import validate_guidance_explanation

    root = _backend_root()
    path = args.input or (root / "data" / "guidance_model_review.json")
    path = path.expanduser()
    if not path.is_absolute():
        path = (root / path).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") or data.get("cases") or []
    if not items:
        print("No items in input JSON.", file=sys.stderr)
        return 2

    openings: list[str] = []
    rows: list[dict[str, object]] = []
    for it in items:
        q = it.get("input") or it.get("query") or ""
        out = it.get("output") or it.get("stream_full_text") or ""
        vid = it.get("id") or ""
        verses = it.get("verses_shown") or it.get("verses_retrieved") or []
        primary = verses[0] if verses else ""
        allowed = set(verses) if verses else {primary}
        profile = analyze_query(q)
        vr = validate_guidance_explanation(
            out,
            primary_citation_key=primary,
            allowed=allowed,
            profile=profile,
        )
        openings.append(_opening_phrase(out))
        rows.append(
            {
                "id": vid,
                "citation_ok": 1.0 if vr.ok else 0.0,
                "completion_ok": 0.0 if any(r.startswith("truncation") or r == "too_short" for r in vr.reasons) else 1.0,
                "grammar_ok": 0.0 if any(r.startswith("grammar") for r in vr.reasons) else 1.0,
                "safety_ok": (
                    1.0
                    if not profile.distress
                    else (
                        0.0
                        if any(
                            r.startswith("distress")
                            for r in vr.reasons
                        )
                        else 1.0
                    )
                ),
                "reasons": list(vr.reasons),
            }
        )

    # Distinctiveness: penalize repeated opening prefixes across items.
    dup = sum(1 for i, a in enumerate(openings) for b in openings[i + 1 :] if a and b and (a in b or b in a or a[:40] == b[:40]))
    dist_score = max(0.0, 1.0 - dup / max(1, len(openings)))

    print(json.dumps({"input_path": str(path), "distinctiveness_score": dist_score, "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
