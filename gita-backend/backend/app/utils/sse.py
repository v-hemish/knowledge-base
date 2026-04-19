"""Server-Sent Events helpers (incremental streaming to clients)."""


def sse_data_line(json_payload: str) -> str:
    """One SSE `data:` frame; payload must already be JSON text."""
    return f"data: {json_payload}\n\n"
