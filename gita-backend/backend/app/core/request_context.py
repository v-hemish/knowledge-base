"""Per-request context (request ID for logs and responses)."""

from __future__ import annotations

import contextvars
from typing import Final

_request_id: Final[contextvars.ContextVar[str | None]] = contextvars.ContextVar(
    "request_id",
    default=None,
)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(value: str | None) -> contextvars.Token[str | None]:
    return _request_id.set(value)


def reset_request_id(token: contextvars.Token[str | None]) -> None:
    _request_id.reset(token)
