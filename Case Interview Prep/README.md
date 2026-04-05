# Base Power — Round 1 coding screen (Python)
 Sat checkin
The live round is often about **~30 minutes** on one realistic problem. These drills are **25 minutes each** so you finish a full pass with a few minutes to narrate tradeoffs—same rhythm as the real slot.

## How to use

1. Open `drills/NN_.../README.md` for the goal and **what an interviewer is testing**.
2. Code in **`practice.py`** until `python practice.py` exits cleanly. Each file has **`--- FILL: ... ---`** blocks: **WHERE** to write code and **WHAT** it must do (remove the `raise NotImplementedError` when you replace it).
3. If stuck, open **`reference.py`** and scroll: every function ends with a **Concepts** block that explains the idea.

## The ten drills

| # | Folder | You practice (interviewer signal) |
|---|--------|-----------------------------------|
| 1 | `drills/01_device_registry` | Domain types, invariants, coordinator over a fleet dict |
| 2 | `drills/02_event_dispatch` | Parse untrusted dicts, dispatch table, small side effects |
| 3 | `drills/03_rate_limit_window` | Time windows, fixed-window limiting, fairness intuition |
| 4 | `drills/04_circuit_breaker` | Explicit state machine, failure budgets, recovery probe |
| 5 | `drills/05_retry_backoff` | Retries, exponential backoff, what is “retryable” |
| 6 | `drills/06_dedupe_window` | Dedup keys, sliding-ish behavior, operational noise |
| 7 | `drills/07_topo_jobs` | DAG, cycle detection, dependency order |
| 8 | `drills/08_rbac_checks` | Authorization as data, audit trail, least privilege |
| 9 | `drills/09_stock_reserve` | Reservations, invariants (no negative available), idempotency hint |
| 10 | `drills/10_deploy_window` | Business rules over time, policy objects, clarity |

**Suggested order:** 1 → 2 → 4 → 3 → 5 → 6 → 7 → 8 → 9 → 10 (harder reliability patterns after warm-up).

**Check solutions:** from `Case Interview Prep`, run `python3 drills/verify_against_reference.py` (confirms each `reference.py` satisfies that drill’s tests).

Company context (optional reading): [telemetry / fleet writeup](https://inside.basepowercompany.com/p/building-a-telemetry-stack-for-the).
