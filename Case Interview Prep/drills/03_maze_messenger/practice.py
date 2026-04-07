"""Game 3 practice: 6 micro-drills (5 min each)."""

from __future__ import annotations

from collections import deque

Point = tuple[int, int]


def find_cell(grid: list[str], ch: str) -> Point:
    """Micro 1: find first cell equal to ch."""
    # --- FILL 1 ---
    raise NotImplementedError


def in_bounds(grid: list[str], r: int, c: int) -> bool:
    """Micro 2: coordinate boundary check."""
    # --- FILL 2 ---
    raise NotImplementedError


def neighbors(grid: list[str], p: Point) -> list[Point]:
    """Micro 3: 4-direction walkable neighbors."""
    # --- FILL 3 ---
    raise NotImplementedError


def shortest_distance(grid: list[str], start: Point, goal: Point) -> int:
    """Micro 4: BFS shortest distance, -1 if unreachable."""
    # --- FILL 4 ---
    raise NotImplementedError


def shortest_path(grid: list[str]) -> list[Point]:
    """Micro 5: BFS path reconstruction from S to G."""
    # --- FILL 5 ---
    raise NotImplementedError


def count_open_regions(grid: list[str]) -> int:
    """Micro 6: number of connected components over non-wall cells."""
    # --- FILL 6 ---
    raise NotImplementedError


if __name__ == "__main__":
    board = [
        "S..#.",
        "##.#.",
        "...#.",
        ".###.",
        "...G.",
    ]
    path = shortest_path(board)
    assert find_cell(board, "S") == (0, 0)
    assert in_bounds(board, 4, 4) is True
    assert in_bounds(board, 9, 9) is False
    assert shortest_distance(board, (0, 0), (4, 3)) == 11
    assert path[0] == (0, 0)
    assert path[-1] == (4, 3)
    assert len(path) == 12

    blocked = [
        "S#G",
        "###",
        "...",
    ]
    assert shortest_path(blocked) == []
    assert count_open_regions(["..#", "#..", "..#"]) == 1
    print("ok")
