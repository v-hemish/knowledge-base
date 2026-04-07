"""
Game 5 solution: Tournament Scoreboard (6 micro-drills)

Theory covered:
- OOP state + behavior grouping
- update logic from events
- stable deterministic sorting
- report generation from domain state
"""

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
        """Micro 3: derived field."""
        return self.goals_for - self.goals_against


class Scoreboard:
    def __init__(self) -> None:
        self.stats: dict[str, TeamStats] = {}

    def ensure_team(self, name: str) -> TeamStats:
        """Micro 1: create-if-missing."""
        if name not in self.stats:
            self.stats[name] = TeamStats()
        return self.stats[name]

    def record_match(self, home: str, away: str, home_goals: int, away_goals: int) -> None:
        """Micro 2: apply match event."""
        h = self.ensure_team(home)
        a = self.ensure_team(away)

        h.played += 1
        a.played += 1
        h.goals_for += home_goals
        h.goals_against += away_goals
        a.goals_for += away_goals
        a.goals_against += home_goals

        if home_goals > away_goals:
            h.wins += 1
            a.losses += 1
            h.points += 3
        elif home_goals < away_goals:
            a.wins += 1
            h.losses += 1
            a.points += 3
        else:
            h.draws += 1
            a.draws += 1
            h.points += 1
            a.points += 1

    def rankings(self) -> list[tuple[str, TeamStats]]:
        """Micro 4: tie-breaker sort."""
        return sorted(
            self.stats.items(),
            key=lambda row: (-row[1].points, -row[1].goal_diff, -row[1].goals_for, row[0]),
        )

    def report_rows(self) -> list[str]:
        """Micro 5: compact ranking table rows."""
        rows: list[str] = []
        for name, s in self.rankings():
            rows.append(f"{name} {s.points} {s.goal_diff} {s.goals_for}")
        return rows

    def top_k(self, k: int) -> list[str]:
        """Micro 6: return top-k names."""
        return [name for name, _ in self.rankings()[:k]]


if __name__ == "__main__":
    sb = Scoreboard()
    sb.record_match("a", "b", 1, 0)
    sb.record_match("a", "c", 0, 2)
    assert [n for n, _ in sb.rankings()] == ["c", "a", "b"]
    print("solution ok")
