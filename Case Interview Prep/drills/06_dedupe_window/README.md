# Drill 6 — Dedupe within a time window (25 min)

**Time box:** 25 minutes.

## What can go away in ~30 minutes

- Multi-host dedupe, Redis TTL, cardinality explosion protection.
- Keep **in-memory** map `key -> last_seen_time`.

## What they are testing

- Turning a **stream** into **signals** (first vs repeat).
- Clear definition of **dedupe key** and **window semantics** (you should state them aloud).

## Your task

Implement `practice.py` until `python practice.py` prints `ok`.

## Stuck?

See `reference.py`.
