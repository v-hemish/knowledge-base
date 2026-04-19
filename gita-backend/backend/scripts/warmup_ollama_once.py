#!/usr/bin/env python3
"""One-shot Ollama chat to reduce cold first-token latency before benchmarks or eval runs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--base-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        help="Ollama base URL (default OLLAMA_BASE_URL or http://127.0.0.1:11434)",
    )
    p.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_MODEL", ""),
        help="Model tag (default OLLAMA_MODEL; required if env unset)",
    )
    args = p.parse_args()
    model = (args.model or "").strip()
    if not model:
        print("error: pass --model or set OLLAMA_MODEL", file=sys.stderr)
        return 1
    base = args.base_url.rstrip("/")
    url = f"{base}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the single word OK."}],
        "stream": False,
        "options": {"num_predict": 8, "temperature": 0.0},
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp.read()
    except urllib.error.URLError as e:
        print(e, file=sys.stderr)
        return 1
    print("warmup_ok", model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
