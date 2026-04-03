"""
Drill 2 — Parse and dispatch (25 min)
Search for "FILL" below. Run: python practice.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Union


@dataclass(frozen=True)
class Telemetry:
    device_id: str
    watts: int


@dataclass(frozen=True)
class Heartbeat:
    device_id: str


@dataclass(frozen=True)
class Fault:
    device_id: str
    code: str


Event = Union[Telemetry, Heartbeat, Fault]


def parse_event(raw: Dict[str, Any]) -> Event:
    """
    Accept raw dicts:
      {"kind": "telemetry", "device_id": str, "watts": int}
      {"kind": "heartbeat", "device_id": str}
      {"kind": "fault", "device_id": str, "code": str}
    Raise ValueError on unknown kind, missing keys, or wrong types.
    """
    # --- FILL: parse_event ---
    # WHERE: body of this function.
    # WHAT: Require key "kind" (str). Branch on kind and build Telemetry / Heartbeat / Fault.
    #       Validate device_id (and watts int, code str) exist and have correct types.
    #       Reject bool for watts (bool is a subclass of int in Python). Unknown kind -> ValueError.
    raise NotImplementedError


@dataclass
class DeviceView:
    last_watts: int | None = None
    fault_count: int = 0


class Processor:
    """Keeps a simple per-device view; updates via apply()."""

    def __init__(self) -> None:
        self._by_device: Dict[str, DeviceView] = {}

    def _ensure(self, device_id: str) -> DeviceView:
        if device_id not in self._by_device:
            self._by_device[device_id] = DeviceView()
        return self._by_device[device_id]

    def apply(self, raw: Dict[str, Any]) -> None:
        """Parse raw; dispatch; mutate state. Raises ValueError like parse_event."""
        # --- FILL: Processor.apply ---
        # WHERE: body of this method.
        # WHAT: ev = parse_event(raw). Dispatch on type(ev):
        #       Telemetry -> set this device's last_watts on its DeviceView.
        #       Heartbeat -> ensure DeviceView exists (touch _ensure), no watt change.
        #       Fault   -> increment fault_count on that DeviceView.
        #       Tip: small private methods _on_telemetry / _on_heartbeat / _on_fault keep this short.
        raise NotImplementedError

    def snapshot(self) -> Dict[str, DeviceView]:
        return dict(self._by_device)


if __name__ == "__main__":
    p = Processor()
    p.apply({"kind": "telemetry", "device_id": "d1", "watts": 120})
    assert p.snapshot()["d1"].last_watts == 120
    p.apply({"kind": "heartbeat", "device_id": "d1"})
    assert p.snapshot()["d1"].last_watts == 120
    p.apply({"kind": "fault", "device_id": "d1", "code": "E_OVERHEAT"})
    assert p.snapshot()["d1"].fault_count == 1
    try:
        parse_event({"kind": "nope"})
        assert False
    except ValueError:
        pass
    try:
        parse_event({"kind": "telemetry", "device_id": "x"})  # missing watts
        assert False
    except ValueError:
        pass
    print("ok")
