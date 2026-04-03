# Drill 9 — Stock and reservations (25 min)

**Time box:** 25 minutes.

## What can go away in ~30 minutes

- Database transactions, optimistic locking, multi-warehouse routing.
- Keep **single location**, **two counters**: `on_hand` and `reserved`.

## What they are testing

- **Invariant**: `reserved <= on_hand` always.
- **Available** as derived state (`on_hand - reserved`), not a third stored field (unless you justify it).

## Your task

Implement `practice.py` until `python practice.py` prints `ok`.

## Stuck?

See `reference.py`.
