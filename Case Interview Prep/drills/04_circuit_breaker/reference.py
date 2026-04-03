"""
Drill 4 — Reference + concepts.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int, open_seconds: float) -> None:
        if failure_threshold < 1 or open_seconds <= 0:
            raise ValueError("invalid breaker config")
        self._threshold = failure_threshold
        self._open_sec = open_seconds
        self._state = CircuitState.CLOSED
        self._fail_streak = 0
        self._open_until: float | None = None

    def state(self) -> CircuitState:
        return self._state

    def _trip_open(self, now: float) -> None:
        self._state = CircuitState.OPEN
        self._open_until = now + self._open_sec
        self._fail_streak = 0

    def call(self, fn: Callable[[], T], now: float) -> T:
        if self._state == CircuitState.OPEN:
            assert self._open_until is not None
            if now < self._open_until:
                raise CircuitOpenError("circuit open")
            self._state = CircuitState.HALF_OPEN

        try:
            out = fn()
        except Exception:
            if self._state == CircuitState.HALF_OPEN:
                self._trip_open(now)
            else:
                self._fail_streak += 1
                if self._fail_streak >= self._threshold:
                    self._trip_open(now)
            raise

        self._fail_streak = 0
        self._state = CircuitState.CLOSED
        self._open_until = None
        return out


# --- Concepts: CircuitBreaker.call ---
# - Three states: CLOSED (normal), OPEN (fail fast), HALF_OPEN (single probe).
# - On success from HALF_OPEN or CLOSED: reset streak and return to CLOSED.
# - On failure in HALF_OPEN: reopen with a fresh cooldown from `now`.
# - On failure in CLOSED: increment streak; trip when threshold reached.
# - Injecting `now` avoids flaky time-based tests; production might use monotonic time.
# - This pattern stops cascading load on a sick dependency while allowing recovery probes.


if __name__ == "__main__":
    cb = CircuitBreaker(1, 5.0)

    def ok() -> str:
        return "ok"

    def boom() -> str:
        raise RuntimeError("x")

    try:
        cb.call(boom, 0.0)
    except RuntimeError:
        pass
    assert cb.state() == CircuitState.OPEN
    assert cb.call(ok, 5.0) == "ok"
    assert cb.state() == CircuitState.CLOSED
    print("reference ok")
