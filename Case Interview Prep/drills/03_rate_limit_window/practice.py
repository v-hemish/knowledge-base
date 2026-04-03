"""
Drill 3 — Fixed-window limiter (25 min)
Search for "FILL" below. Windows align to multiples of window_seconds from t=0.
Run: python practice.py
"""

from __future__ import annotations


class FixedWindowLimiter:
    """
    At most `max_calls` allowed per fixed window of `window_seconds`.
    `now` is a float seconds clock (like time.monotonic() or a test clock).
    """

    def __init__(self, max_calls: int, window_seconds: float) -> None:
        if max_calls < 1 or window_seconds <= 0:
            raise ValueError("invalid limiter config")
        self._max = max_calls
        self._w = window_seconds
        self._window_start: float | None = None
        self._used = 0

    def allow(self, now: float) -> bool:
        """Return True if call is permitted and count it; False if over limit."""
        # --- FILL: FixedWindowLimiter.allow ---
        # WHERE: body of this method (you may reset self._window_start / self._used as needed).
        # WHAT: Current window index = int(now // self._w). Window starts at index * self._w.
        #       When the window changes from the last one you counted, reset used count to 0.
        #       If used < self._max: increment used, return True. Else return False.
        raise NotImplementedError


if __name__ == "__main__":
    L = FixedWindowLimiter(2, 10.0)
    assert L.allow(0.0) is True
    assert L.allow(1.0) is True
    assert L.allow(2.0) is False
    assert L.allow(10.0) is True
    assert L.allow(11.0) is True
    assert L.allow(12.0) is False
    assert L.allow(20.0) is True
    assert L.allow(29.9) is True
    assert L.allow(30.0) is True
    assert L.allow(31.0) is True
    assert L.allow(32.0) is False
    assert L.allow(40.0) is True
    print("ok")
