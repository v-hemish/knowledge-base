"""
Drill 10 — Deploy time policy (25 min)
Search for "FILL" below. Run: python practice.py
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Set


def deploy_allowed(when: datetime, blackout_dates: Set[date]) -> bool:
    """
    Return True iff all hold:
      - when.date() not in blackout_dates
      - weekday is Monday-Friday (Monday=0 ... Sunday=6)
      - hour in [9, 17)  (9:00 up to but not including 17:00, naive local clock)
    """
    # --- FILL: deploy_allowed ---
    # WHERE: body of this function.
    # WHAT: Return False if when.date() is in blackout_dates.
    #       Return False if when.weekday() is Saturday or Sunday (5 or 6).
    #       Return False unless 9 <= when.hour < 17 (hour only; minutes ignored for this drill).
    #       Otherwise return True.
    raise NotImplementedError


if __name__ == "__main__":
    fri = datetime(2026, 4, 3, 10, 0)
    sat = datetime(2026, 4, 4, 10, 0)
    assert deploy_allowed(fri, set()) is True
    assert deploy_allowed(sat, set()) is False
    assert deploy_allowed(datetime(2026, 4, 3, 8, 59), set()) is False
    assert deploy_allowed(datetime(2026, 4, 3, 16, 59), set()) is True
    assert deploy_allowed(datetime(2026, 4, 3, 17, 0), set()) is False
    black = {date(2026, 4, 3)}
    assert deploy_allowed(fri, black) is False
    print("ok")
