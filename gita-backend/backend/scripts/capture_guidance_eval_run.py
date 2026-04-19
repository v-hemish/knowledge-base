#!/usr/bin/env python3
"""
Capture guidance stream I/O for each query in data/guidance_review_queries.json.

Usage (from backend/, with API and Ollama running):
  export OLLAMA_MODEL=qwen2.5:14b   # or qwen2.5:32b — restart backend after changing
  python scripts/capture_guidance_eval_run.py --out data/guidance_model_review.json

Use ``--debug`` to send ``eval_debug: true`` so the API records Ollama/stream diagnostics in
``completed.eval`` and does not mask failures with the generic fallback paragraph.

Each captured item includes ``client_wall_ms`` (HTTP client wall time). When the API returns
``completed.latency_ms``, that object is copied to the item for per-stage server timings.

**Batch order:** the first query in ``items`` is often the first Ollama call after idle, so
``first_ollama_token_ms_from_request_start`` can look like an outlier (model load / GPU wake).
Compare against ``latency_ms.ollama_seconds_since_previous_stream_end`` in server logs; run a
throwaway warmup request or shuffle query order when benchmarking.

Very long first-token times (20–35s) can still appear at moderate prompt sizes when the runner
was idle, the GPU had to reload weights, or another job contended for Ollama—that is not fixed
by trimming the text alone; treat as infrastructure / batching.

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


def _warmup_ollama(base_url: str, model: str) -> None:
    """One tiny /api/chat call so the first real query is not measuring Ollama cold start."""
    model = (model or "").strip()
    if not model:
        print("warmup: skipped (no model; set OLLAMA_MODEL or --ollama-model)", file=sys.stderr)
        return
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the single word OK."}],
        "stream": False,
        "options": {"num_predict": 8, "temperature": 0.0},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            resp.read()
    except Exception as exc:
        print(f"warmup: failed ({exc})", file=sys.stderr)
        return
    print(f"warmup: ok ({int((time.perf_counter() - t0) * 1000)} ms, {model})", file=sys.stderr)


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
    p.add_argument(
        "--warmup",
        action="store_true",
        help=(
            "Fire a single throwaway /api/chat to Ollama before the batch so the first real "
            "query is not measuring cold-start (burnout TTFT outlier). Requires OLLAMA_MODEL "
            "or --ollama-model, and uses --ollama-base-url for the Ollama host."
        ),
    )
    p.add_argument(
        "--ollama-model",
        default=os.environ.get("OLLAMA_MODEL", ""),
        help="Model tag used for --warmup (default OLLAMA_MODEL).",
    )
    p.add_argument(
        "--ollama-base-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        help="Ollama host used for --warmup (default OLLAMA_BASE_URL or http://127.0.0.1:11434).",
    )
    args = p.parse_args(argv)

    if args.warmup:
        _warmup_ollama(args.ollama_base_url, args.ollama_model)

    root = _backend_root()
    qpath = args.queries or (root / "data" / "guidance_review_queries.json")
    qpath = qpath if qpath.is_absolute() else (root / qpath).resolve()
    data = json.loads(qpath.read_text(encoding="utf-8"))
    items_in = data.get("items") or []
    if not items_in:
        print("No items in queries file.", file=sys.stderr)
        return 2

    url = f"{args.base_url.rstrip('/')}/api/v1/guidance/stream"
    model_note = os.environ.get("OLLAMA_MODEL", "unknown-from-env")

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
            "model": (meta or {}).get("ollama_model"),
            "ollama_model_env_note": model_note,
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
            f"Wrote diagnostics to {failed_path}. Start the API and Ollama, then retry; "
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
