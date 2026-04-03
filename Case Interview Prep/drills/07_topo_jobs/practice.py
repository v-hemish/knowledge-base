"""
Drill 7 — Topological order (25 min)
Search for "FILL" below. Run: python practice.py
"""

from __future__ import annotations

from typing import Dict, Iterable, List


class CycleError(Exception):
    pass


def topo_order(jobs: Dict[str, Iterable[str]]) -> List[str]:
    """
    `jobs[job_id]` lists prerequisite job ids that must appear before `job_id`.
    Return any valid linear order containing every key exactly once.
    Raise CycleError if a cycle exists (including self-loop).
    """
    # --- FILL: topo_order ---
    # WHERE: body of this function.
    # WHAT: Nodes = every job id in jobs plus every id appearing in any dependency list.
    #       Build indegree for each node and adjacency: for each edge prereq -> job, indegree[job]++.
    #       Kahn: queue nodes with indegree 0 (sorted(queue) keeps tests deterministic), pop,
    #       append to output, relax outgoing edges. If output length < len(nodes), raise CycleError.
    #       Return output list (each node exactly once).
    raise NotImplementedError


if __name__ == "__main__":
    assert topo_order({"a": [], "b": ["a"], "c": ["b"]}) == ["a", "b", "c"]
    o = topo_order({"x": ["y"], "y": ["z"], "z": []})
    assert o.index("z") < o.index("y") < o.index("x")
    try:
        topo_order({"a": ["b"], "b": ["a"]})
        assert False
    except CycleError:
        pass
    try:
        topo_order({"solo": ["solo"]})
        assert False
    except CycleError:
        pass
    print("ok")
