# Drill 10 — Deploy allowed in time window (25 min)

**Time box:** 25 minutes.

## What can go away in ~30 minutes

- Time zones, holiday calendars from HR, canary stages, manual approvals.
- Keep **naive `datetime`** (no tz), **hour-level** rule, **date blacklist**.

## What they are testing

- Encoding **business rules** clearly and **testing** them with concrete instants.
- Separating **policy** (`deploy_allowed`) from hypothetical callers.

## Your task

Implement `practice.py` until `python practice.py` prints `ok`.

## Stuck?

See `reference.py`.
