import sqlite3
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request

from app.core.config import Settings, get_settings
from app.core.rate_limit import guidance_rate_limiter
from app.db.database import connect


def get_settings_dep() -> Settings:
    return get_settings()


def check_guidance_rate_limit(
    request: Request,
    settings: Settings = Depends(get_settings_dep),
) -> None:
    """Lightweight per-IP cap on guidance endpoints (in-memory, process-local)."""
    limit = settings.guidance_rate_limit_per_minute
    if limit <= 0:
        return
    key = request.client.host if request.client else "unknown"
    ok, retry_after = guidance_rate_limiter().allow(key, limit=limit, window_s=60.0)
    if ok:
        return
    ra = max(1, int(retry_after) + 1)
    raise HTTPException(
        status_code=429,
        detail={
            "error": "rate_limit_exceeded",
            "message": "Too many guidance requests from this client. Try again shortly.",
            "retry_after_s": ra,
        },
        headers={"Retry-After": str(ra)},
    )


def get_db_conn(settings: Settings = Depends(get_settings_dep)) -> Generator[sqlite3.Connection, None, None]:
    try:
        conn = connect(settings.resolved_database_path())
    except OSError as exc:
        raise HTTPException(
            status_code=503,
            detail={"message": "Could not open database file.", "type": "db_os_error"},
        ) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=503,
            detail={"message": "Database connection failed.", "type": "db_sqlite_error"},
        ) from exc
    try:
        yield conn
    finally:
        conn.close()
