"""
Drill 10 — Reference + concepts.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Set


def deploy_allowed(when: datetime, blackout_dates: Set[date]) -> bool:
    if when.date() in blackout_dates:
        return False
    if when.weekday() >= 5:
        return False
    if not (9 <= when.hour < 17):
        return False
    return True


# --- Concepts: deploy_allowed ---
# - **Policy as pure function** of inputs makes unit tests trivial and avoids hidden globals.
# - Naive datetimes are fine in interviews if you **say** "production: store UTC, convert to org TZ".
# - Half-open hour range [9,17) matches "business hours until 5pm" without debating 16:59:59.
# - Blackout dates are a simple set; real systems load from config or API with audit on changes.


if __name__ == "__main__":
    assert deploy_allowed(datetime(2026, 4, 3, 12, 0), set()) is True
    print("reference ok")
