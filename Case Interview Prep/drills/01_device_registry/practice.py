"""
Drill 1 — Device registry (25 min)
Search for "FILL" below. Each block says WHERE to code and WHAT it must do.
Run: python practice.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class DeviceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


@dataclass
class Device:
    device_id: str
    status: DeviceStatus


class Registry:
    """Fleet registry: unique devices, status updates, simple queries."""

    def __init__(self) -> None:
        self._devices: Dict[str, Device] = {}

    def register(self, device_id: str, initial: DeviceStatus = DeviceStatus.OFFLINE) -> None:
        """Register a new device. Raise ValueError if device_id already exists."""
        # --- FILL: Registry.register ---
        # WHERE: body of this method (replace the raise).
        # WHAT: If device_id is already a key in self._devices, raise ValueError.
        #       Otherwise store Device(device_id=device_id, status=initial).
        raise NotImplementedError

    def set_status(self, device_id: str, new_status: DeviceStatus) -> None:
        """Set status if device exists; raise KeyError if unknown device_id."""
        # --- FILL: Registry.set_status ---
        # WHERE: body of this method.
        # WHAT: If device_id not in self._devices, raise KeyError(device_id).
        #       Otherwise replace that entry with a new Device(same id, new_status).
        raise NotImplementedError

    def get(self, device_id: str) -> Optional[Device]:
        """Return Device or None if not registered."""
        # --- FILL: Registry.get ---
        # WHERE: body of this method.
        # WHAT: Return self._devices.get(device_id) (or equivalent).
        raise NotImplementedError

    def count_by_status(self) -> Dict[DeviceStatus, int]:
        """Count devices per status (include zeros only for statuses that appear)."""
        # --- FILL: Registry.count_by_status ---
        # WHERE: body of this method.
        # WHAT: One pass over self._devices values; count how many per DeviceStatus.
        #       Only include statuses with count > 0 (do not put 0-count keys in the dict).
        raise NotImplementedError


if __name__ == "__main__":
    r = Registry()
    r.register("gw-1", DeviceStatus.OFFLINE)
    r.register("gw-2", DeviceStatus.ONLINE)
    try:
        r.register("gw-1")
        assert False, "duplicate register should raise"
    except ValueError:
        pass
    r.set_status("gw-1", DeviceStatus.ONLINE)
    assert r.get("gw-1") == Device("gw-1", DeviceStatus.ONLINE)
    try:
        r.set_status("missing", DeviceStatus.ONLINE)
        assert False
    except KeyError:
        pass
    counts = r.count_by_status()
    assert counts[DeviceStatus.ONLINE] == 2
    assert DeviceStatus.OFFLINE not in counts
    r.register("gw-3", DeviceStatus.DEGRADED)
    counts2 = r.count_by_status()
    assert counts2[DeviceStatus.DEGRADED] == 1
    print("ok")
