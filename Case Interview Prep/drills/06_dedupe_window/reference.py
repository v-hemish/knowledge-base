"""
Drill 6 — Reference + concepts.
"""


class Deduper:
    def __init__(self, window_seconds: float) -> None:
        if window_seconds <= 0:
            raise ValueError("window must be positive")
        self._w = window_seconds
        self._last: dict[str, float] = {}

    def classify(self, key: str, now: float) -> str:
        prev = self._last.get(key)
        if prev is not None and now - prev < self._w:
            return "suppressed"
        self._last[key] = now
        return "emitted"


# --- Concepts: Deduper.classify ---
# - Dedupe key is your **definition of sameness** (source + type + fingerprint in real systems).
# - Window compares **elapsed time since last emitted**, not wall-clock buckets (this is closer to
#   a simple suppression timer than a fixed-window counter).
# - Tradeoff: memory grows with unique keys; production uses TTL stores or capped LRU sets.
# - Pair with **escalation** if repeats exceed N within a window (see alert processors in the wild).


if __name__ == "__main__":
    d = Deduper(1.0)
    assert d.classify("x", 0.0) == "emitted" and d.classify("x", 0.5) == "suppressed"
    print("reference ok")
