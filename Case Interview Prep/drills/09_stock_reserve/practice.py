"""
Drill 9 — Reservations (25 min)
Search for "FILL" below. Run: python practice.py
"""

from __future__ import annotations


class Stock:
    """
    Per SKU:
      on_hand: physical count
      reserved: promised to open work (installs, holds)
    available = on_hand - reserved (not stored separately).
    """

    def __init__(self) -> None:
        self._on: dict[str, int] = {}
        self._res: dict[str, int] = {}

    def set_on_hand(self, sku: str, qty: int) -> None:
        """Admin sets physical stock; must not drop below current reserved."""
        # --- FILL: Stock.set_on_hand ---
        # WHERE: body of this method.
        # WHAT: Let r = current reserved for sku (0 if missing). If qty < r, raise ValueError.
        #       Set self._on[sku] = qty.
        raise NotImplementedError

    def available(self, sku: str) -> int:
        # --- FILL: Stock.available ---
        # WHERE: body of this method.
        # WHAT: Return on_hand(sku) - reserved(sku), treating missing keys as 0.
        raise NotImplementedError

    def reserve(self, sku: str, qty: int) -> bool:
        """If available >= qty, increase reserved by qty and return True; else False."""
        # --- FILL: Stock.reserve ---
        # WHERE: body of this method.
        # WHAT: If qty < 0 or available(sku) < qty, return False.
        #       Else add qty to self._res[sku] and return True.
        raise NotImplementedError

    def release(self, sku: str, qty: int) -> None:
        """Decrease reserved by qty, never below 0."""
        # --- FILL: Stock.release ---
        # WHERE: body of this method.
        # WHAT: Decrease self._res[sku] by qty, clamp so result is never negative.
        raise NotImplementedError


if __name__ == "__main__":
    s = Stock()
    s.set_on_hand("inv", 10)
    assert s.available("inv") == 10
    assert s.reserve("inv", 4) is True
    assert s.available("inv") == 6
    assert s.reserve("inv", 7) is False
    s.release("inv", 1)
    assert s.available("inv") == 7
    try:
        s.set_on_hand("inv", 2)
        assert False
    except ValueError:
        pass
    s.set_on_hand("inv", 8)
    assert s.available("inv") == 5
    print("ok")
