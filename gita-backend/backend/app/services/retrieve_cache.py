"""Tiny TTL cache for retrieve-only responses (same process, no invalidation on DB writes)."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict

from app.schemas.guidance_retrieve import RetrieveGuidanceResponse


class _RetrieveResponseCache:
    """LRU + TTL; safe for concurrent reads/writes from async workers on one thread pool."""

    def __init__(self, *, max_entries: int, ttl_s: float) -> None:
        self._max = max(0, max_entries)
        self._ttl = max(0.0, ttl_s)
        self._lock = threading.Lock()
        self._data: OrderedDict[str, tuple[float, RetrieveGuidanceResponse]] = OrderedDict()

    def disabled(self) -> bool:
        return self._max <= 0 or self._ttl <= 0.0

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def get(self, key: str) -> RetrieveGuidanceResponse | None:
        if self.disabled():
            return None
        now = time.monotonic()
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires_at, payload = item
            if expires_at <= now:
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return payload

    def set(self, key: str, value: RetrieveGuidanceResponse) -> None:
        if self.disabled():
            return
        now = time.monotonic()
        expires = now + self._ttl
        with self._lock:
            if key in self._data:
                del self._data[key]
            self._data[key] = (expires, value)
            self._data.move_to_end(key)
            while len(self._data) > self._max:
                self._data.popitem(last=False)


_cache: _RetrieveResponseCache | None = None
_cache_lock = threading.Lock()


def configure_retrieve_cache(*, max_entries: int, ttl_s: float) -> None:
    global _cache
    with _cache_lock:
        _cache = _RetrieveResponseCache(max_entries=max_entries, ttl_s=ttl_s)


def retrieve_cache_get(key: str) -> RetrieveGuidanceResponse | None:
    c = _cache
    if c is None or c.disabled():
        return None
    return c.get(key)


def retrieve_cache_set(key: str, value: RetrieveGuidanceResponse) -> None:
    c = _cache
    if c is None or c.disabled():
        return
    c.set(key, value)


def retrieve_cache_clear() -> None:
    """Drop all cached retrieve responses (e.g. after tests or admin reload)."""
    c = _cache
    if c is None:
        return
    c.clear()
