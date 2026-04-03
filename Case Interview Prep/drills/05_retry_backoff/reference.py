"""
Drill 5 — Reference + concepts.
"""

from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


class TransientError(Exception):
    pass


def call_with_retries(
    fn: Callable[[], T],
    *,
    max_attempts: int,
    base_delay_s: float,
    on_wait: Callable[[float], None],
) -> T:
    last: TransientError | None = None
    transient_failures = 0
    for attempt in range(max_attempts):
        try:
            return fn()
        except TransientError as e:
            last = e
            if attempt + 1 >= max_attempts:
                break
            delay = base_delay_s * (2**transient_failures)
            transient_failures += 1
            on_wait(delay)
        except Exception:
            raise
    assert last is not None
    raise last


# --- Concepts: call_with_retries ---
# - Retries only make sense for **idempotent** operations or those with external idempotency keys.
# - Exponential backoff: delay = base * 2**k spreads out load on a struggling dependency.
# - `on_wait` injection keeps tests fast and deterministic (record delays instead of sleeping).
# - Non-transient errors should **fail fast**; swallowing them hides bugs.
# - Jitter (randomized delay) is a common production tweak to avoid thundering herds.


if __name__ == "__main__":
    delays: list[float] = []

    def record_wait(d: float) -> None:
        delays.append(d)

    state = {"k": 0}

    def flaky() -> str:
        state["k"] += 1
        if state["k"] < 2:
            raise TransientError("x")
        return "ok"

    assert call_with_retries(flaky, max_attempts=3, base_delay_s=2.0, on_wait=record_wait) == "ok"
    assert delays == [2.0]
    print("reference ok")
