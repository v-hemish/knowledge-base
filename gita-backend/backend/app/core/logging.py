import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.request_context import get_request_id


class JsonLogFormatter(logging.Formatter):
    """Minimal structured logging without extra dependencies."""

    def format(self, record: logging.LogRecord) -> str:
        rid = getattr(record, "request_id", None) or get_request_id()
        payload: dict[str, Any] = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if rid:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Merge `extra=` keys (excluding internal logging attrs)
        reserved = logging.LogRecord("", 0, "", 0, None, None, None).__dict__.keys()
        for key, value in record.__dict__.items():
            if key not in reserved and key not in payload and not key.startswith("_"):
                try:
                    json.dumps(value)
                    payload[key] = value
                except TypeError:
                    payload[key] = repr(value)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger once (JSON lines to stdout). Unknown levels fall back to INFO."""
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root.addHandler(handler)
    name = (level or "INFO").strip().upper()
    try:
        root.setLevel(name)
    except ValueError:
        root.setLevel(logging.INFO)
