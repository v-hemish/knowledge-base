"""
Drill 4 — Circuit breaker (25 min)
Search for "FILL" below. Run: python practice.py
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
    """
    CLOSED: calls pass through; count consecutive failures.
    After `failure_threshold` failures -> OPEN until `now >= opened_at + open_seconds`.
    Then HALF_OPEN: one trial call; success -> CLOSED; failure -> OPEN again (new cooldown from `now`).
    """

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

    def call(self, fn: Callable[[], T], now: float) -> T:
        """Invoke fn() or raise CircuitOpenError when OPEN and still cooling down."""
        # --- FILL: CircuitBreaker.call ---
        # WHERE: body of this method (only place you implement state transitions for this drill).
        # WHAT:
        #   OPEN + now < self._open_until  -> raise CircuitOpenError (do not call fn).
        #   OPEN + now >= open_until       -> treat as HALF_OPEN for this single attempt (then call fn).
        #   CLOSED                         -> call fn.
        #   On fn success: set CLOSED, clear fail streak, clear open_until, return result.
        #   On fn failure in HALF_OPEN: reopen OPEN with self._open_until = now + self._open_sec.
        #   On fn failure in CLOSED: increment fail streak; if streak >= threshold, go OPEN
        #       and set open_until = now + open_seconds (and reset streak if your design needs it).
        #   Re-raise the original exception after recording failure.
        raise NotImplementedError


if __name__ == "__main__":
    def ok() -> str:
        return "ok"

    def boom() -> str:
        raise RuntimeError("down")

    cb = CircuitBreaker(2, 10.0)
    assert cb.call(ok, now=0.0) == "ok"
    assert cb.state() == CircuitState.CLOSED
    try:
        cb.call(boom, now=1.0)
        assert False
    except RuntimeError:
        pass
    assert cb.state() == CircuitState.CLOSED
    try:
        cb.call(boom, now=2.0)
        assert False
    except RuntimeError:
        pass
    assert cb.state() == CircuitState.OPEN
    try:
        cb.call(ok, now=3.0)
        assert False
    except CircuitOpenError:
        pass
    assert cb.call(ok, now=12.0) == "ok"
    assert cb.state() == CircuitState.CLOSED

    cb2 = CircuitBreaker(1, 5.0)
    try:
        cb2.call(boom, now=0.0)
        assert False
    except RuntimeError:
        pass
    assert cb2.state() == CircuitState.OPEN
    assert cb2.call(ok, now=5.0) == "ok"
    assert cb2.state() == CircuitState.CLOSED

    cb3 = CircuitBreaker(1, 5.0)
    try:
        cb3.call(boom, now=0.0)
        assert False
    except RuntimeError:
        pass
    try:
        cb3.call(boom, now=5.0)
        assert False
    except RuntimeError:
        pass
    assert cb3.state() == CircuitState.OPEN
    try:
        cb3.call(ok, now=6.0)
        assert False
    except CircuitOpenError:
        pass
    assert cb3.call(ok, now=10.0) == "ok"
    assert cb3.state() == CircuitState.CLOSED
    print("ok")
