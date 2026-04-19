"""Attach a request ID to each request, response headers, and logging context."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import reset_request_id, set_request_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Accept ``X-Request-ID`` or generate one; expose on ``request.state`` and response headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get("x-request-id")
        rid = incoming.strip() if incoming and incoming.strip() else str(uuid.uuid4())
        if len(rid) > 128:
            rid = str(uuid.uuid4())
        request.state.request_id = rid
        token = set_request_id(rid)
        try:
            response = await call_next(request)
        finally:
            reset_request_id(token)
        response.headers["X-Request-ID"] = rid
        return response
