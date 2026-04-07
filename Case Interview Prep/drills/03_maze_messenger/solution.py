"""
Game 3 solution: Maze Messenger (6 micro-drills)

Theory covered:
- coordinate utilities
- graph traversal on grids
- BFS distance and path reconstruction
- connected component counting
"""

from __future__ import annotations

from collections import deque

Point = tuple[int, int]


def find_cell(grid: list[str], ch: str) -> Point:
    """Micro 1: locate marker."""
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == ch:
                return (r, c)
    raise ValueError(f"{ch} not found")


def in_bounds(grid: list[str], r: int, c: int) -> bool:
    """Micro 2: boundary utility."""
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def neighbors(grid: list[str], p: Point) -> list[Point]:
    """Micro 3: valid non-wall neighbors."""
    r, c = p
    out: list[Point] = []
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if in_bounds(grid, nr, nc) and grid[nr][nc] != "#":
            out.append((nr, nc))
    return out


def shortest_distance(grid: list[str], start: Point, goal: Point) -> int:
    """Micro 4: BFS distance."""
    q = deque([(start, 0)])
    seen = {start}
    while q:
        cur, dist = q.popleft()
        if cur == goal:
            return dist
        for nxt in neighbors(grid, cur):
            if nxt in seen:
                continue
            seen.add(nxt)
            q.append((nxt, dist + 1))
    return -1


def shortest_path(grid: list[str]) -> list[Point]:
    """Micro 5: BFS shortest path from S to G."""
    start = find_cell(grid, "S")
    goal = find_cell(grid, "G")
    q = deque([start])
    prev: dict[Point, Point | None] = {start: None}

    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for nxt in neighbors(grid, cur):
            if nxt in prev:
                continue
            prev[nxt] = cur
            q.append(nxt)

    if goal not in prev:
        return []

    out: list[Point] = []
    node: Point | None = goal
    while node is not None:
        out.append(node)
        node = prev[node]
    out.reverse()
    return out


def count_open_regions(grid: list[str]) -> int:
    """Micro 6: count connected components among non-wall cells."""
    seen: set[Point] = set()
    regions = 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == "#" or (r, c) in seen:
                continue
            regions += 1
            q = deque([(r, c)])
            seen.add((r, c))
            while q:
                cur = q.popleft()
                for nxt in neighbors(grid, cur):
                    if nxt not in seen:
                        seen.add(nxt)
                        q.append(nxt)
    return regions


if __name__ == "__main__":
    b = ["SG"]
    assert shortest_path(b) == [(0, 0), (0, 1)]
    print("solution ok")
