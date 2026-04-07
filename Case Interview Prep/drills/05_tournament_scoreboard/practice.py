"""Game 5 practice: 6 micro-drills (5 min each)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TeamStats:
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    points: int = 0
    goals_for: int = 0
    goals_against: int = 0

    @property
    def goal_diff(self) -> int:
        # --- FILL 3 ---
        raise NotImplementedError


class Scoreboard:
    def __init__(self) -> None:
        self.stats: dict[str, TeamStats] = {}

    def ensure_team(self, name: str) -> TeamStats:
        """Micro 1: create-if-missing and return stats object."""
        # --- FILL 1 ---
        raise NotImplementedError

    def record_match(self, home: str, away: str, home_goals: int, away_goals: int) -> None:
        """Micro 2: apply one match result."""
        # --- FILL 2 ---
        raise NotImplementedError

    def rankings(self) -> list[tuple[str, TeamStats]]:
        """Micro 4: sorted standings with tie-breakers."""
        # --- FILL 4 ---
        raise NotImplementedError

    def report_rows(self) -> list[str]:
        """Micro 5: produce 'team pts gd gf' rows in ranking order."""
        # --- FILL 5 ---
        raise NotImplementedError

    def top_k(self, k: int) -> list[str]:
        """Micro 6: return first k team names from rankings."""
        # --- FILL 6 ---
        raise NotImplementedError


if __name__ == "__main__":
    sb = Scoreboard()
    sb.record_match("dragons", "wolves", 2, 0)
    sb.record_match("wolves", "phoenix", 1, 1)
    sb.record_match("phoenix", "dragons", 3, 3)

    ordered = [name for name, _ in sb.rankings()]
    assert ordered == ["dragons", "phoenix", "wolves"]
    assert sb.stats["dragons"].points == 4
    assert sb.stats["wolves"].points == 1
    assert sb.stats["dragons"].goal_diff == 2
    assert sb.report_rows()[0].startswith("dragons 4 ")
    assert sb.top_k(2) == ["dragons", "phoenix"]
    print("ok")
