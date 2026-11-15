"""API settings, read from the environment (see `.env.example`)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from .repository import ClickHouseRepository, FieldRepository, FileRepository


def _flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    data_source: str = "files"  # "files" | "clickhouse"
    cors_origins: tuple[str, ...] = ("http://localhost:3004",)
    allow_sample_preview: bool = True

    @classmethod
    def from_env(cls) -> Settings:
        origins = os.environ.get("AGROCYCLE_CORS_ORIGINS", "http://localhost:3004")
        return cls(
            data_source=os.environ.get("AGROCYCLE_DATA_SOURCE", "files"),
            cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
            allow_sample_preview=_flag("AGROCYCLE_ALLOW_SAMPLE_PREVIEW", True),
        )


def build_repository(settings: Settings) -> FieldRepository:
    if settings.data_source == "clickhouse":
        # Imported here so the API starts without boto3 or clickhouse-connect when using files.
        from common.config import clickhouse_client

        return ClickHouseRepository(clickhouse_client())
    if settings.data_source == "files":
        return FileRepository()
    raise RuntimeError(f"AGROCYCLE_DATA_SOURCE must be 'files' or 'clickhouse', got {settings.data_source!r}")
