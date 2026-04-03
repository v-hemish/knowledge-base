# Drill 3 — Fixed-window rate limit (25 min)

**Time box:** 25 minutes.

## What can go away in ~30 minutes

- Distributed Redis limiter, fairness across tenants, token refill math proofs.
- Keep **one process**, **explicit `now` parameter** (testable, no hidden clock).

## What they are testing

- Reasoning about **time buckets** and **state reset**.
- Clear API: `allow(now) -> bool` that **consumes** a slot when True.
- You can name the tradeoff vs **sliding window** or **token bucket**.

## Your task

Implement `practice.py` until `python practice.py` prints `ok`.

## Stuck?

Open `reference.py` for the full solution and Concepts sections.
