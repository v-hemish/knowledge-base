"""
Game 4 solution: Boss Retry Arena (6 micro-drills)

Theory covered:
- retryability classification
- bounded retries
- backoff progression
- small utility functions that keep retry loop readable
"""

from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


class RetryableBossError(Exception):
    pass


def is_retryable_code(code: str) -> bool:
    """Micro 1: retryable error classifier."""
    return code in {"TIMEOUT", "THROTTLED", "TEMP_UNAVAILABLE"}


def backoff_delay(base_delay: float, retry_index: int) -> float:
    """Micro 2: exponential backoff helper."""
    return base_delay * (2**retry_index)


def should_retry(attempt: int, max_attempts: int) -> bool:
    """Micro 3: attempt gate."""
    return attempt < max_attempts


def run_with_backoff(
    fn: Callable[[], T],
    *,
    max_attempts: int,
    base_delay: float,
    on_wait: Callable[[float], None],
) -> T:
    """Micro 4: bounded retry loop with backoff callback."""
    if max_attempts <= 0:
        raise ValueError("max_attempts must be > 0")

    last_retryable: RetryableBossError | None = None
    retries_so_far = 0

    for attempt in range(max_attempts):
        try:
            return fn()
        except RetryableBossError as exc:
            last_retryable = exc
            if not should_retry(attempt + 1, max_attempts):
                break
            delay = backoff_delay(base_delay, retries_so_far)
            retries_so_far += 1
            on_wait(delay)
        except Exception:
            raise

    assert last_retryable is not None
    raise last_retryable


def format_attempt_log(attempt: int, err: Exception) -> str:
    """Micro 5: stable one-line log format."""
    return f"attempt={attempt} error={err.__class__.__name__}:{err}"


def retry_budget_used(total_attempts: int, max_attempts: int) -> str:
    """Micro 6: used-attempt ratio as percent."""
    if max_attempts <= 0:
        raise ValueError("max_attempts must be > 0")
    pct = int((total_attempts / max_attempts) * 100)
    return f"{pct}%"


if __name__ == "__main__":
    events: list[float] = []
    idx = {"n": 0}

    def w(d: float) -> None:
        events.append(d)

    def unstable() -> str:
        idx["n"] += 1
        if idx["n"] <= 2:
            raise RetryableBossError("retry")
        return "ok"

    assert run_with_backoff(unstable, max_attempts=3, base_delay=1.0, on_wait=w) == "ok"
    assert events == [1.0, 2.0]
    print("solution ok")
