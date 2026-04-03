# Drill 4 — Circuit breaker core (25 min)

**Time box:** 25 minutes.

## What can go away in ~30 minutes

- Distributed/shared breaker state, metrics exporters, per-endpoint configs.
- Keep **in-memory**, **injectable `now`**, **synchronous** `call`.

## What they are testing

- A real **state machine** (CLOSED / OPEN / HALF_OPEN).
- **Failure budget** and **cooldown** behavior you can explain in one sentence each.
- **Half-open** as a deliberate probe, not “hope it works.”

## Your task

Implement `practice.py` until `python practice.py` prints `ok`.

## Stuck?

See `reference.py`.
