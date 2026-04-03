"""
Drill 5 — Retry + exponential backoff (25 min)
Search for "FILL" below. Run: python practice.py
"""

from __future__ import annotations

from typing import Callable, List, TypeVar

T = TypeVar("T")


class TransientError(Exception):
    """Raise this from fn to signal a retryable failure."""


def call_with_retries(
    fn: Callable[[], T],
    *,
    max_attempts: int,
    base_delay_s: float,
    on_wait: Callable[[float], None],
) -> T:
    """
    Call fn until it returns or you exhaust attempts.
    - On success: return the value.
    - On TransientError: wait `base_delay_s * 2**k` seconds before the next attempt,
      where k is the number of transient failures so far (k starts at 0 before first retry).
      Call on_wait(delay) for each wait (tests record delays; no real sleep required).
    - On any other exception: propagate immediately (no retry).
    If all attempts consume TransientError, re-raise the last TransientError.
    """
    # --- FILL: call_with_retries ---
    # WHERE: body of this function.
    # WHAT: Loop up to max_attempts. Try fn().
    #       Return on success. On TransientError: if attempts left, call
    #       on_wait(base_delay_s * (2**k)) where k = number of transient failures so far
    #       starting at 0 for the first wait, then 1, ...; then retry.
    #       If no attempts left after a TransientError, re-raise that error.
    #       On any other Exception: re-raise immediately (no wait, no retry).
    raise NotImplementedError


if __name__ == "__main__":
    delays: List[float] = []

    def record_wait(d: float) -> None:
        delays.append(d)

    state = {"n": 0}

    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise TransientError("no")
        return "yes"

    delays.clear()
    state["n"] = 0
    assert call_with_retries(flaky, max_attempts=4, base_delay_s=1.0, on_wait=record_wait) == "yes"
    assert delays == [1.0, 2.0]

    def always_bad() -> str:
        raise TransientError("x")

    delays.clear()
    try:
        call_with_retries(always_bad, max_attempts=2, base_delay_s=0.5, on_wait=record_wait)
        assert False
    except TransientError:
        pass
    assert delays == [0.5]

    def fatal() -> str:
        raise ValueError("nope")

    try:
        call_with_retries(fatal, max_attempts=3, base_delay_s=1.0, on_wait=record_wait)
        assert False
    except ValueError:
        pass
    print("ok")
