"""
Game 1 solution: Space Cargo (6 micro-drills)

Theory covered:
- parsing untrusted input
- input validation
- invariant checks
- small single-purpose functions
- readable composition in a dispatcher
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CargoState:
    capacity: int
    loaded: dict[str, int]
    total_weight: int = 0


def parse_command(raw: str) -> tuple[str, tuple[str, ...]]:
    """Micro 1: parse LOAD/UNLOAD/STATUS commands."""
    tokens = raw.strip().split()
    if not tokens:
        raise ValueError("empty command")

    cmd = tokens[0].upper()
    if cmd == "LOAD" and len(tokens) == 3:
        return cmd, (tokens[1], tokens[2])
    if cmd == "UNLOAD" and len(tokens) == 2:
        return cmd, (tokens[1],)
    if cmd == "STATUS" and len(tokens) == 1:
        return cmd, ()
    raise ValueError("malformed command")


def to_positive_int(text: str) -> int:
    """Micro 2: parse positive integer values."""
    try:
        value = int(text)
    except ValueError as exc:
        raise ValueError("must be int") from exc
    if value <= 0:
        raise ValueError("must be > 0")
    return value


def can_load(state: CargoState, weight: int) -> bool:
    """Micro 3: check capacity guard."""
    return state.total_weight + weight <= state.capacity


def load_item(state: CargoState, item_id: str, weight: int) -> str:
    """Micro 4: apply load state transition."""
    if item_id in state.loaded:
        raise ValueError("item already loaded")
    if not can_load(state, weight):
        raise ValueError("capacity exceeded")
    state.loaded[item_id] = weight
    state.total_weight += weight
    return f"loaded {item_id}"


def unload_item(state: CargoState, item_id: str) -> str:
    """Micro 5: apply unload transition."""
    if item_id not in state.loaded:
        raise ValueError("item not loaded")
    state.total_weight -= state.loaded[item_id]
    del state.loaded[item_id]
    return f"unloaded {item_id}"


def status_line(state: CargoState) -> str:
    """Micro 6: produce reporting text."""
    return f"count={len(state.loaded)}, weight={state.total_weight}/{state.capacity}"


def apply_command(state: CargoState, raw: str) -> str:
    """Compose micro-drills into end-to-end command handling."""
    cmd, args = parse_command(raw)
    if cmd == "STATUS":
        return status_line(state)
    if cmd == "LOAD":
        return load_item(state, args[0], to_positive_int(args[1]))
    if cmd == "UNLOAD":
        return unload_item(state, args[0])
    raise ValueError("unsupported command")


if __name__ == "__main__":
    s = CargoState(capacity=6, loaded={})
    assert apply_command(s, "LOAD a 2") == "loaded a"
    assert apply_command(s, "LOAD b 3") == "loaded b"
    assert apply_command(s, "STATUS") == "count=2, weight=5/6"
    print("solution ok")
