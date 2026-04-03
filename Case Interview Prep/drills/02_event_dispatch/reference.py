"""
Drill 2 — Reference + concepts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Union


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


def _req_str(d: Dict[str, Any], key: str) -> str:
    if key not in d:
        raise ValueError(f"missing {key}")
    v = d[key]
    if not isinstance(v, str):
        raise ValueError(f"{key} must be str")
    return v


def _req_int(d: Dict[str, Any], key: str) -> int:
    if key not in d:
        raise ValueError(f"missing {key}")
    v = d[key]
    if not isinstance(v, int) or isinstance(v, bool):
        raise ValueError(f"{key} must be int")
    return v


def parse_event(raw: Dict[str, Any]) -> Event:
    if "kind" not in raw:
        raise ValueError("missing kind")
    kind = raw["kind"]
    if not isinstance(kind, str):
        raise ValueError("kind must be str")
    if kind == "telemetry":
        return Telemetry(
            device_id=_req_str(raw, "device_id"),
            watts=_req_int(raw, "watts"),
        )
    if kind == "heartbeat":
        return Heartbeat(device_id=_req_str(raw, "device_id"))
    if kind == "fault":
        return Fault(device_id=_req_str(raw, "device_id"), code=_req_str(raw, "code"))
    raise ValueError(f"unknown kind: {kind}")


# --- Concepts: parse_event ---
# - Single choke point for validation keeps handlers trustworthy.
# - isinstance(..., bool): bool subclasses int in Python; reject so {"watts": True} fails.
# - Small helpers (_req_*) keep error messages consistent.


@dataclass
class DeviceView:
    last_watts: int | None = None
    fault_count: int = 0


class Processor:
    def __init__(self) -> None:
        self._by_device: Dict[str, DeviceView] = {}

    def _ensure(self, device_id: str) -> DeviceView:
        if device_id not in self._by_device:
            self._by_device[device_id] = DeviceView()
        return self._by_device[device_id]

    def _on_telemetry(self, e: Telemetry) -> None:
        v = self._ensure(e.device_id)
        v.last_watts = e.watts

    def _on_heartbeat(self, e: Heartbeat) -> None:
        self._ensure(e.device_id)

    def _on_fault(self, e: Fault) -> None:
        v = self._ensure(e.device_id)
        v.fault_count += 1

    def apply(self, raw: Dict[str, Any]) -> None:
        ev = parse_event(raw)
        handlers: Dict[type, Callable[[Any], None]] = {
            Telemetry: self._on_telemetry,
            Heartbeat: self._on_heartbeat,
            Fault: self._on_fault,
        }
        handlers[type(ev)](ev)

    def snapshot(self) -> Dict[str, DeviceView]:
        return dict(self._by_device)


# --- Concepts: Processor.apply ---
# - Dispatch on type(ev) avoids stringly-typed branching after parse.
# - New event type: add dataclass, parse branch, one handler, one dict entry.
# - match/case on type(ev) is a readable alternative in Python 3.10+.


if __name__ == "__main__":
    p = Processor()
    p.apply({"kind": "telemetry", "device_id": "d1", "watts": 5})
    assert p.snapshot()["d1"].last_watts == 5
    print("reference ok")
