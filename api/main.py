"""FastAPI app. Run from the repository root:  uv run uvicorn api.main:app --reload --port 8000"""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import logging_config

logging_config.configure()
_log = logging.getLogger("agrocycle")

from .db.imagery import ImagerySource
from .db.repository import FieldRepository
from .routes import router
from .settings import Settings, build_clickhouse_client, build_imagery, build_repository

_DESCRIPTION = """
AgroCycle helps Iowa farmers compare three crop-rotation strategies — 2-year corn/soy,
3-year corn/soy/oat, and 4-year corn/soy/oat/alfalfa — using their field's real environmental
data. It never scores, ranks or recommends; it returns *worth exploring*, *qualified comparison*
or *abstention* with the evidence behind each outcome.

## Key design constraints

- **No recommendations.** The engine abstains whenever the data is insufficient. No score, no winner.
- **Grounded AI (F1).** The `/ask` endpoints answer questions about stored results using only the
  context already returned — the model sees nothing else.
- **Data version.** Every response carries `data_version` (the latest ClickHouse `load_id`).
  GET 200 responses also carry `ETag` and `Cache-Control: public, max-age=3600`.
- **Pilot area.** Only Story and Boone counties, Iowa. Fields outside this area are rejected at
  the validation step.

## Errors

All errors share one shape:
```json
{"error": {"code": "not_found", "message": "No field with id 'x'.", "details": {}}}
```
"""

_TAGS = [
    {"name": "meta", "description": "Health check and configuration options."},
    {"name": "fields", "description": "Field lookup, polygon upload, profile and time-series."},
    {"name": "compare", "description": "Run the rotation comparison and retrieve stored analyses."},
    {"name": "evidence", "description": "Published research that underpins the engine's rules."},
    {"name": "methods", "description": "Indicator lineage, data sources and glossary."},
    {"name": "ask", "description": "F1 — Ask AgroCycle: grounded AI answers about a stored result or field profile."},
]


def create_app(
    settings: Settings | None = None,
    repository: FieldRepository | None = None,
    imagery: ImagerySource | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="AgroCycle API",
        version="1.0.0",
        description=_DESCRIPTION,
        openapi_tags=_TAGS,
        contact={"name": "AgroCycle — NASA Space Apps 2026", "url": "https://agrocycle.praxicraft.com"},
        license_info={"name": "MIT"},
        docs_url="/docs",
        redoc_url=None,  # served manually below so we can set a custom page title
    )
    app.state.settings = settings
    repo = repository or build_repository(settings)
    app.state.repository = repo
    app.state.ch_client = build_clickhouse_client(settings)
    app.state.imagery = imagery or build_imagery(settings)

    # Populate data_version at startup
    try:
        app.state.data_version = repo.data_version
    except Exception:
        app.state.data_version = "unknown"

    _log.info(
        "AgroCycle API starting",
        extra={
            "data_source": settings.data_source,
            "data_version": app.state.data_version,
            "repository": getattr(repo, "name", type(repo).__name__),
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    # ── Request logging middleware ────────────────────────────────────────────
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        if request.url.path in ("/api/v1/health", "/health"):
            return await call_next(request)

        req_id = uuid.uuid4().hex[:12]
        request.state.req_id = req_id

        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "-")
        )

        start = time.monotonic()
        exc_to_reraise = None
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as exc:
            exc_to_reraise = exc

        duration_ms = round((time.monotonic() - start) * 1000)

        extra = dict(
            req_id=req_id,
            method=request.method,
            path=request.url.path,
            status=status,
            duration_ms=duration_ms,
            client_ip=client_ip,
        )

        if exc_to_reraise is not None:
            _log.error(
                "%s %s → 500 (%d ms)",
                request.method, request.url.path, duration_ms,
                exc_info=exc_to_reraise, extra=extra,
            )
            raise exc_to_reraise

        log_fn = _log.warning if status >= 400 else _log.info
        log_fn("%s %s → %d (%d ms)", request.method, request.url.path, status, duration_ms, extra=extra)

        response.headers["X-Request-ID"] = req_id
        return response

    # ETag / Cache-Control middleware for GET 200 responses
    @app.middleware("http")
    async def etag_middleware(request: Request, call_next):
        response = await call_next(request)
        if request.method == "GET" and response.status_code == 200:
            dv = getattr(app.state, "data_version", "unknown")
            response.headers["ETag"] = f'"{dv}"'
            response.headers["Cache-Control"] = "public, max-age=3600"
        return response

    # Exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code = {404: "not_found", 422: "validation_error", 503: "service_unavailable"}.get(exc.status_code, "error")
        if exc.status_code >= 500:
            _log.error("HTTP %d: %s", exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": code, "message": str(exc.detail), "details": {}}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        _log.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "message": "Invalid request.", "details": {"errors": exc.errors()}}},
        )

    app.include_router(router, prefix="/api/v1")
    # Also mount at root so existing tests and callers that have not migrated yet still work.
    app.include_router(router)

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html() -> HTMLResponse:
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="AgroCycle API — Reference",
            redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    return app


app = create_app()
