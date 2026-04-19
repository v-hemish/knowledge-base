"""FastAPI application factory and ASGI entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.health import router as health_router
from app.api.routes.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.database import connect, init_schema
from app.middleware.request_id import RequestIdMiddleware
from app.retrieval.embedding_store import load_embedding_index, set_embedding_index
from app.services.retrieve_cache import configure_retrieve_cache

_log = logging.getLogger("app.main")


def _attach_request_id(payload: dict, request: Request) -> dict:
    rid = getattr(request.state, "request_id", None)
    if rid:
        payload["request_id"] = rid
    return payload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open DB for schema init, load embedding index, and release resources on shutdown."""
    settings = get_settings()
    setup_logging(settings.log_level)
    configure_retrieve_cache(
        max_entries=settings.retrieve_cache_max_entries,
        ttl_s=settings.retrieve_cache_ttl_s,
    )
    db_path = settings.resolved_database_path()
    conn = connect(db_path)
    try:
        init_schema(conn)
    finally:
        conn.close()
    emb = load_embedding_index(settings)
    if settings.semantic_rerank_enabled and emb is None:
        _log.warning(
            "semantic_rerank_enabled_but_no_artifact",
            extra={"path": str(settings.resolved_embeddings_npz_path())},
        )
    _log.info(
        "startup_complete",
        extra={
            "db_path": str(db_path),
            "environment": settings.environment,
            "embeddings_loaded": emb is not None,
        },
    )
    try:
        yield
    finally:
        set_embedding_index(None)
        _log.info("shutdown_complete")


def create_app() -> FastAPI:
    settings = get_settings()
    # Ensure retrieve cache exists even when the app is used without ASGI lifespan
    # (e.g. ``TestClient(create_app())`` without ``with`` — Starlette only runs lifespan in ``__enter__``).
    configure_retrieve_cache(
        max_entries=settings.retrieve_cache_max_entries,
        ttl_s=settings.retrieve_cache_ttl_s,
    )
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)

    cors_origins = settings.cors_origins()
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        body = _attach_request_id(
            {"detail": jsonable_encoder(exc.errors()), "error": "validation_error"},
            request,
        )
        return JSONResponse(status_code=422, content=body)

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if not isinstance(detail, str | dict):
            detail = str(detail)
        body: dict = {"detail": detail, "error": "http_error"}
        if (
            exc.status_code == 429
            and isinstance(detail, dict)
            and detail.get("error") == "rate_limit_exceeded"
        ):
            body["error"] = "rate_limit_exceeded"
        _attach_request_id(body, request)
        hdrs = dict(exc.headers) if exc.headers else None
        return JSONResponse(status_code=exc.status_code, content=body, headers=hdrs)

    app.include_router(health_router)
    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app()
