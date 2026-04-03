# Drill 7 — Job order with dependencies (25 min)

**Time box:** 25 minutes.

## What can go away in ~30 minutes

- Parallel worker pools, persistence, partial reruns, dynamic DAG edits.
- Keep **static graph**, **all job ids known upfront**.

## What they are testing

- **Cycle detection** before you run anything expensive.
- **Topological order** (Kahn or DFS postorder)—either is fine if correct and explained.

## Your task

Implement `practice.py` until `python practice.py` prints `ok`.

## Stuck?

See `reference.py`.
