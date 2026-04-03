"""
Drill 9 — Reference + concepts.
"""


class Stock:
    def __init__(self) -> None:
        self._on: dict[str, int] = {}
        self._res: dict[str, int] = {}

    def set_on_hand(self, sku: str, qty: int) -> None:
        res = self._res.get(sku, 0)
        if qty < res:
            raise ValueError("on_hand cannot be below reserved")
        self._on[sku] = qty

    def available(self, sku: str) -> int:
        return self._on.get(sku, 0) - self._res.get(sku, 0)

    def reserve(self, sku: str, qty: int) -> bool:
        if qty < 0:
            return False
        if self.available(sku) < qty:
            return False
        self._res[sku] = self._res.get(sku, 0) + qty
        return True

    def release(self, sku: str, qty: int) -> None:
        cur = self._res.get(sku, 0)
        self._res[sku] = max(0, cur - qty)


# --- Concepts: Stock ---
# - **Reservation pattern** splits "physically here" vs "promised" so multiple workers do not
#   oversell the same units.
# - `available` is derived to avoid drift between three stored counters.
# - `set_on_hand` rejects shrinking below reserved—mirrors receiving a cycle count that conflicts
#   with open holds (interview bonus: mention DB transaction + row lock).
# - Next steps: order-id keyed holds, expiry, idempotent reserve with client token.


if __name__ == "__main__":
    s = Stock()
    s.set_on_hand("x", 5)
    assert s.reserve("x", 5) and s.available("x") == 0
    print("reference ok")
