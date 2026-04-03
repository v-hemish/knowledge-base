# Drill 2 — Parse and dispatch events (25 min)

**Time box:** 25 minutes.

## What can go away in ~30 minutes

- gRPC/proto, persistence, async, metrics backends.
- Keep **one process**, **dict-shaped payloads**, **explicit rejects**.

## What they are testing

- **Untrusted input** → validate types and required keys.
- **Dispatch** without a giant `if/elif` chain (table or match/case).
- **Localized state** updated only by well-typed events.

## Your task

Implement `practice.py` until `python practice.py` prints `ok`.

## Stuck?

See `reference.py` — Concepts blocks follow each function.
