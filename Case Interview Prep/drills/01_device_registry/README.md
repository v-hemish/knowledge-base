# Drill 1 — Device registry (25 min)

**Time box:** 25 minutes (targets a ~30 minute live round with narration buffer).

## What can go away in a real 30-minute screen

- Persistent database, auth, HTTP layer, threading.
- Full battery physics; keep **IDs, status, and simple aggregates**.

## What they are testing

- Clean **types** (`Enum`, `dataclass`) instead of string soup.
- **Coordinator** (`Registry`) that enforces rules (no duplicate IDs, valid transitions).
- You **state assumptions** aloud (e.g. “degraded can go offline”).

## Your task

Implement `practice.py` so `python practice.py` passes all assertions.

## Stuck?

Open `reference.py`. Each function has a **Concepts** comment block after it.
