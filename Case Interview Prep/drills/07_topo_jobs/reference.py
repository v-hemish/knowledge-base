"""
Drill 7 — Reference + concepts.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List


class CycleError(Exception):
    pass


def topo_order(jobs: Dict[str, Iterable[str]]) -> List[str]:
    nodes = set(jobs.keys()) | {d for deps in jobs.values() for d in deps}
    indeg = {n: 0 for n in nodes}
    adj = {n: [] for n in nodes}
    for j, deps in jobs.items():
        for d in deps:
            adj[d].append(j)
            indeg[j] += 1

    q = deque(sorted(n for n in nodes if indeg[n] == 0))
    out: List[str] = []
    while q:
        u = q.popleft()
        out.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

    if len(out) != len(nodes):
        raise CycleError("cycle detected")
    return out


# --- Concepts: topo_order ---
# - Prerequisites `d` for job `j` mean edge `d -> j` (d finishes before j starts).
# - Kahn's algorithm: repeatedly peel nodes with indegree 0; if you cannot drain all nodes,
#   a directed cycle exists.
# - Sorting the initial zero-indegree set (and tie-breaking) yields **deterministic** order for tests;
#   in production you might use priority for fairness.
# - DFS with postorder + gray set is an alternative cycle detection + topo in one pass.


if __name__ == "__main__":
    assert topo_order({"a": [], "b": ["a"]}) == ["a", "b"]
    print("reference ok")
