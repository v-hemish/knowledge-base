"""
Drill 1 — Reference solution + concepts (read when stuck).
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
    def __init__(self) -> None:
        self._devices: Dict[str, Device] = {}

    def register(self, device_id: str, initial: DeviceStatus = DeviceStatus.OFFLINE) -> None:
        if device_id in self._devices:
            raise ValueError(f"duplicate device_id: {device_id}")
        self._devices[device_id] = Device(device_id=device_id, status=initial)

    # Concepts: register
    # - Coordinator owns the dict; entity is a small dataclass.
    # - Fail fast on duplicate IDs (explicit error type helps callers).
    # - Enum for status avoids typos and documents the domain vocabulary.

    def set_status(self, device_id: str, new_status: DeviceStatus) -> None:
        if device_id not in self._devices:
            raise KeyError(device_id)
        d = self._devices[device_id]
        self._devices[device_id] = Device(device_id=d.device_id, status=new_status)

    # Concepts: set_status
    # - dataclass is immutable here: replace the whole Device instead of mutating fields
    #   (fewer shared-mutation bugs; easy to reason about in an interview).
    # - KeyError vs None return: pick one policy and say it aloud in the interview.

    def get(self, device_id: str) -> Optional[Device]:
        return self._devices.get(device_id)

    # Concepts: get
    # - Optional return documents "might not exist" in the type system.

    def count_by_status(self) -> Dict[DeviceStatus, int]:
        out: Dict[DeviceStatus, int] = {}
        for d in self._devices.values():
            out[d.status] = out.get(d.status, 0) + 1
        return out

    # Concepts: count_by_status
    # - Aggregation in one pass O(n); interviewer may ask how you'd do this at scale
    #   (stream, database GROUP BY, metrics pipeline).


if __name__ == "__main__":
    r = Registry()
    r.register("a", DeviceStatus.OFFLINE)
    r.set_status("a", DeviceStatus.ONLINE)
    assert r.count_by_status()[DeviceStatus.ONLINE] == 1
    print("reference ok")
