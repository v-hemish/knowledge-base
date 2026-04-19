"""Fixed-window-ish in-memory rate limiting (per client IP, process-local)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict


class InMemorySlidingRateLimiter:
    """
    Drop timestamps older than ``window_s``; allow at most ``limit`` events per key per window.

    Thread-safe; intended for small MVP traffic (no Redis).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, list[float]] = defaultdict(list)

    def reset(self) -> None:
        """Clear all counters (for tests)."""
        with self._lock:
            self._hits.clear()

    def allow(self, key: str, *, limit: int, window_s: float) -> tuple[bool, float]:
        """
        Returns ``(allowed, retry_after_s)``. When not allowed, ``retry_after_s`` is a hint
        for when the oldest counted request ages out of the window.
        """
        now = time.monotonic()
        cutoff = now - window_s
        with self._lock:
            times = [t for t in self._hits[key] if t >= cutoff]
            if len(times) >= limit:
                oldest = min(times)
                retry_after = max(0.0, window_s - (now - oldest))
                self._hits[key] = times
                return False, retry_after
            times.append(now)
            self._hits[key] = times
        return True, 0.0


_guidance_limiter = InMemorySlidingRateLimiter()


def guidance_rate_limiter() -> InMemorySlidingRateLimiter:
    return _guidance_limiter
