#!/usr/bin/env python3
"""
Capture guidance stream I/O for each query in a review JSON (default: data/guidance_review_queries.json).

For a full core + edge suite, use:
  data/guidance_comprehensive_review_queries.json

Usage (from backend/, with API running and OPENAI_API_KEY set):
  python scripts/capture_guidance_eval_run.py --out data/guidance_model_review.json

  python scripts/capture_guidance_eval_run.py \\
    --queries data/guidance_comprehensive_review_queries.json \\
    --out data/guidance_model_review_comprehensive.json

Use ``--debug`` to send ``eval_debug: true`` so the API records generation/stream diagnostics in
``completed.eval`` and does not mask failures with the generic fallback paragraph.

Each captured item includes ``client_wall_ms`` (HTTP client wall time). When the API returns
``completed.latency_ms``, that object is copied to the item for per-stage server timings.

Compare two JSON files side by side with your own review or scripts/score_guidance_output_eval.py.

If every request fails and ``--out`` already exists, the script writes ``*_failed_<timestamp>.json``
next to ``--out`` and exits non-zero unless you pass ``--clobber-on-total-failure``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Capture guidance /stream outputs for eval queries.")
    p.add_argument(
        "--queries",
        type=Path,
        default=None,
        help="JSON with items[{id,query}] (default: data/guidance_review_queries.json).",
    )
    p.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output JSON path (e.g. data/guidance_model_review.json).",
    )
    p.add_argument(
        "--base-url",
        default=os.environ.get("GUIDANCE_API_BASE", "http://127.0.0.1:8000"),
        help="API base URL (default GUIDANCE_API_BASE or http://127.0.0.1:8000).",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Send eval_debug=true; capture completed.eval, errors[], and omit generic fallback masking.",
    )
    p.add_argument(
        "--clobber-on-total-failure",
        action="store_true",
        help=(
            "Write to --out even when every item failed. Default: if --out already exists, "
            "write a sidecar *_failed_<timestamp>.json instead so a good capture is not wiped."
        ),
    )
    args = p.parse_args(argv)

    root = _backend_root()
    qpath = args.queries or (root / "data" / "guidance_review_queries.json")
    qpath = qpath if qpath.is_absolute() else (root / qpath).resolve()
    data = json.loads(qpath.read_text(encoding="utf-8"))
    items_in = data.get("items") or []
    if not items_in:
        print("No items in queries file.", file=sys.stderr)
        return 2

    url = f"{args.base_url.rstrip('/')}/api/v1/guidance/stream"
    model_note = os.environ.get("OPENAI_MODEL", "unknown-from-env")

    results: list[dict] = []
    for it in items_in:
        qid = it.get("id", "")
        q = it.get("query", "")
        payload = {"query": q, "eval_debug": True} if args.debug else {"query": q}
        body = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        meta, verses, chunks, completed, errors = None, [], [], {}, []
        t_client0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=420) as r:
                for raw in r:
                    line = raw.decode().strip()
                    if not line.startswith("data: "):
                        continue
                    ev = json.loads(line[6:])
                    t, d = ev.get("event"), ev.get("data", {})
                    if t == "metadata":
                        meta = d
                    elif t == "verses":
                        verses = [v.get("citation_key") for v in d.get("verses", [])]
                    elif t == "token":
                        chunks.append(d.get("text", ""))
                    elif t == "error":
                        errors.append(d)
                    elif t == "completed":
                        completed = d or {}
        except Exception as exc:
            results.append(
                {
                    "id": qid,
                    "input": q,
                    "error": str(exc),
                    "client_wall_ms": int((time.perf_counter() - t_client0) * 1000),
                }
            )
            continue
        client_wall_ms = int((time.perf_counter() - t_client0) * 1000)
        row: dict = {
            "id": qid,
            "input": q,
            "model": (meta or {}).get("model"),
            "openai_model_env_note": model_note,
            "verses_shown": verses,
            "output": "".join(chunks).strip(),
            "completed": completed,
            "client_wall_ms": client_wall_ms,
        }
        if isinstance(completed, dict) and completed.get("latency_ms"):
            row["latency_ms"] = completed["latency_ms"]
        if args.debug:
            row["errors"] = errors
            row["eval"] = completed.get("eval") if isinstance(completed, dict) else None
        results.append(row)

    out = {
        "schema": "guidance_eval_capture_v2" if args.debug else "guidance_eval_capture_v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "queries_path": str(qpath),
        "items": results,
    }
    out_path = args.out if args.out.is_absolute() else (root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, ensure_ascii=False, indent=2)
    all_failed = bool(results) and all("error" in r for r in results)
    if all_failed and out_path.exists() and not args.clobber_on_total_failure:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        failed_path = out_path.with_name(f"{out_path.stem}_failed_{ts}{out_path.suffix}")
        failed_path.write_text(text, encoding="utf-8")
        print(
            f"All {len(results)} requests failed; refused to overwrite {out_path}. "
            f"Wrote diagnostics to {failed_path}. Start the API and verify OPENAI_API_KEY, then retry; "
            f"or pass --clobber-on-total-failure to overwrite anyway.",
            file=sys.stderr,
        )
        print(str(failed_path))
        return 1

    out_path.write_text(text, encoding="utf-8")
    print(str(out_path))
    return 0 if not all_failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
