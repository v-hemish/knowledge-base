"""
Drill 3 — Reference + concepts.
"""

from __future__ import annotations


class FixedWindowLimiter:
    def __init__(self, max_calls: int, window_seconds: float) -> None:
        if max_calls < 1 or window_seconds <= 0:
            raise ValueError("invalid limiter config")
        self._max = max_calls
        self._w = window_seconds
        self._window_start: float | None = None
        self._used = 0

    def allow(self, now: float) -> bool:
        idx = int(now // self._w)
        start = idx * self._w
        if self._window_start is None or start != self._window_start:
            self._window_start = start
            self._used = 0
        if self._used < self._max:
            self._used += 1
            return True
        return False


# --- Concepts: FixedWindowLimiter.allow ---
# - Fixed window: bucket key is floor(now / window_seconds). Same bucket shares one counter.
# - When the bucket changes, reset the counter (new window).
# - Injecting `now` makes the logic deterministic in tests; in prod you might wrap time.monotonic().
# - Tradeoff: a burst at the boundary of two windows gets 2*max in a short span; sliding windows
#   smooth that; token bucket allows steady-state burst size control.


if __name__ == "__main__":
    L = FixedWindowLimiter(2, 10.0)
    assert L.allow(0.0) and L.allow(1.0) and not L.allow(2.0)
    print("reference ok")
