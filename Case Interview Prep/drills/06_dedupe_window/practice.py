"""
Drill 6 — Dedupe window (25 min)
Search for "FILL" below. Run: python practice.py
"""

from __future__ import annotations


class Deduper:
    """
    If the same `key` is seen again within `window_seconds` of the last accepted sighting,
    return "suppressed". Otherwise return "emitted" and record this sighting time.
    """

    def __init__(self, window_seconds: float) -> None:
        if window_seconds <= 0:
            raise ValueError("window must be positive")
        self._w = window_seconds
        self._last: dict[str, float] = {}

    def classify(self, key: str, now: float) -> str:
        """Return exactly "emitted" or "suppressed"."""
        # --- FILL: Deduper.classify ---
        # WHERE: body of this method.
        # WHAT: Look up last accepted time for key in self._last.
        #       If previous exists and (now - previous) < self._w, return "suppressed".
        #       Else set self._last[key] = now and return "emitted".
        raise NotImplementedError


if __name__ == "__main__":
    d = Deduper(10.0)
    assert d.classify("a", 0.0) == "emitted"
    assert d.classify("a", 1.0) == "suppressed"
    assert d.classify("a", 9.9) == "suppressed"
    assert d.classify("a", 10.0) == "emitted"
    assert d.classify("b", 10.0) == "emitted"
    assert d.classify("b", 100.0) == "emitted"
    print("ok")
