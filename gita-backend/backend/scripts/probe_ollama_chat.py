#!/usr/bin/env python3
"""
Probe Ollama /api/chat streaming for the configured model (diagnoses empty streams, HTTP errors).

Usage (from backend/):
  export OLLAMA_MODEL=qwen2.5:32b
  export OLLAMA_BASE_URL=http://127.0.0.1:11434   # optional
  uv run python scripts/probe_ollama_chat.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time

import httpx


async def main() -> int:
    p = argparse.ArgumentParser(description="Stream one short chat completion from Ollama.")
    p.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_MODEL", "qwen2.5:32b"),
        help="Model tag (default: OLLAMA_MODEL or qwen2.5:32b).",
    )
    p.add_argument(
        "--base-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        help="Ollama base URL.",
    )
    args = p.parse_args()
    url = f"{args.base_url.rstrip('/')}/api/chat"
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        "stream": True,
        "options": {"num_predict": 32, "temperature": 0.1},
    }
    print(f"POST {url}", file=sys.stderr)
    print(f"model={args.model!r}", file=sys.stderr)

    t0 = time.perf_counter()
    chunks = 0
    buf: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream("POST", url, json=payload) as resp:
                print(f"HTTP {resp.status_code}", file=sys.stderr)
                if resp.status_code >= 400:
                    body = await resp.aread()
                    snippet = body[:800].decode("utf-8", errors="replace")
                    print(snippet, file=sys.stderr)
                    if resp.status_code == 404 and "not found" in snippet.lower():
                        print(
                            f"\nHint: install the model locally, then retry:\n"
                            f"  ollama pull {args.model}\n"
                            f"  ollama list    # use the exact name shown\n",
                            file=sys.stderr,
                        )
                    return 2

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        print("non-json line:", line[:200], file=sys.stderr)
                        continue
                    if obj.get("error"):
                        print("stream error field:", obj["error"], file=sys.stderr)
                        return 3
                    if obj.get("done"):
                        break
                    piece = (obj.get("message") or {}).get("content") or ""
                    if piece:
                        chunks += 1
                        buf.append(piece)
    except httpx.ConnectError as e:
        print("ConnectError:", e, file=sys.stderr)
        return 4
    except httpx.HTTPError as e:
        print("HTTPError:", e, file=sys.stderr)
        return 5

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    text = "".join(buf).strip()
    print(f"first_chunk_latency_ms≈{elapsed_ms if chunks else 'n/a'}", file=sys.stderr)
    print(f"stream_chunk_count={chunks}", file=sys.stderr)
    print("assistant:", repr(text[:500]))
    return 0 if chunks > 0 and text else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
