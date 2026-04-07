"""Game 1 practice: 6 micro-drills (5 min each)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CargoState:
    capacity: int
    loaded: dict[str, int]
    total_weight: int = 0


def parse_command(raw: str) -> tuple[str, tuple[str, ...]]:
    """Micro 1: parse LOAD/UNLOAD/STATUS commands."""
    # --- FILL 1 ---
    raise NotImplementedError


def to_positive_int(text: str) -> int:
    """Micro 2: convert string to positive int."""
    # --- FILL 2 ---
    raise NotImplementedError


def can_load(state: CargoState, weight: int) -> bool:
    """Micro 3: capacity check."""
    # --- FILL 3 ---
    raise NotImplementedError


def load_item(state: CargoState, item_id: str, weight: int) -> str:
    """Micro 4: load one item with invariant checks."""
    # --- FILL 4 ---
    raise NotImplementedError


def unload_item(state: CargoState, item_id: str) -> str:
    """Micro 5: unload one item."""
    # --- FILL 5 ---
    raise NotImplementedError


def status_line(state: CargoState) -> str:
    """Micro 6: render a readable status."""
    # --- FILL 6 ---
    raise NotImplementedError


def apply_command(state: CargoState, raw: str) -> str:
    """Composition step: wire together the six micro functions."""
    cmd, args = parse_command(raw)
    if cmd == "STATUS":
        return status_line(state)
    if cmd == "LOAD":
        return load_item(state, args[0], to_positive_int(args[1]))
    if cmd == "UNLOAD":
        return unload_item(state, args[0])
    raise NotImplementedError


if __name__ == "__main__":
    s = CargoState(capacity=10, loaded={})

    assert apply_command(s, "STATUS") == "count=0, weight=0/10"
    assert apply_command(s, "LOAD ore 4") == "loaded ore"
    assert apply_command(s, "LOAD water 6") == "loaded water"
    assert apply_command(s, "STATUS") == "count=2, weight=10/10"
    assert apply_command(s, "UNLOAD ore") == "unloaded ore"
    assert apply_command(s, "STATUS") == "count=1, weight=6/10"

    assert can_load(s, 1) is True

    try:
        to_positive_int("0")
        assert False
    except ValueError:
        pass

    print("ok")
