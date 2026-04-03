# Drill 5 — Retry with exponential backoff (25 min)

**Time box:** 25 minutes.

## What can go away in ~30 minutes

- Jittered backoff, per-error-class policies, circuit breaker integration, logging.
- Keep **synchronous** calls, **explicit retryable exception type**.

## What they are testing

- **Which failures are transient** vs fatal.
- **Backoff growth** (linear or exponential) without sleeping in unit tests (inject `on_wait`).

## Your task

Implement `practice.py` until `python practice.py` prints `ok`.

## Stuck?

See `reference.py`.
