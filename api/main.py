"""FastAPI app. Run from the repository root:  uv run uvicorn api.main:app --reload --port 8000"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .repository import FieldRepository
from .routes import router
from .settings import Settings, build_repository


def create_app(
    settings: Settings | None = None, repository: FieldRepository | None = None
) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="AgroCycle API",
        version="0.1.0",
        description=(
            "Decision support for crop rotation. It returns a comparison, a qualified comparison or "
            "an abstention, never a recommendation, a score or a ranking."
        ),
    )
    app.state.settings = settings
    app.state.repository = repository or build_repository(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(router)
    return app


app = create_app()
