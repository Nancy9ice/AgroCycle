"""API settings, read from the environment (see `.env.example`)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .repository import ClickHouseRepository, FieldRepository, FileRepository


def _flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    data_source: str = "files"  # "files" | "clickhouse"
    cors_origins: tuple[str, ...] = ("http://localhost:3004",)
    allow_sample_preview: bool = True
    # Where DS2's runner wrote field_indicators.csv; None means the repository default (data/out/indicators).
    indicators_dir: Path | None = None

    @classmethod
    def from_env(cls) -> Settings:
        origins = os.environ.get("AGROCYCLE_CORS_ORIGINS", "http://localhost:3004")
        return cls(
            data_source=os.environ.get("AGROCYCLE_DATA_SOURCE", "files"),
            cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
            allow_sample_preview=_flag("AGROCYCLE_ALLOW_SAMPLE_PREVIEW", True),
            indicators_dir=Path(d) if (d := os.environ.get("AGROCYCLE_INDICATORS_DIR")) else None,
        )


def build_repository(settings: Settings) -> FieldRepository:
    if settings.data_source == "clickhouse":
        # Imported here so the API starts without boto3 or clickhouse-connect when using files.
        from common.config import clickhouse_client

        # Crop sequence and soil series come from the committed notes: see ClickHouseRepository.
        return ClickHouseRepository(clickhouse_client(), notes=FileRepository())
    if settings.data_source == "files":
        return FileRepository(indicators_dir=settings.indicators_dir) if settings.indicators_dir else FileRepository()
    raise RuntimeError(f"AGROCYCLE_DATA_SOURCE must be 'files' or 'clickhouse', got {settings.data_source!r}")


def build_clickhouse_client(settings: Settings):
    """Returns a ClickHouse client for direct queries, or None in file mode."""
    if settings.data_source == "clickhouse":
        from common.config import clickhouse_client
        return clickhouse_client()
    return None


def build_imagery(settings: Settings):
    """The aerial-photo source. Only the database mode has one: it reads `naip_tiles` and the chips in S3.

    If S3 is not configured the API still starts and says there are no photos, rather than failing to boot.
    """
    from .db.imagery import ClickHouseS3Imagery, NoImagery

    if settings.data_source != "clickhouse":
        return NoImagery()
    try:
        from common.config import clickhouse_client, s3_bucket, s3_client

        return ClickHouseS3Imagery(clickhouse_client(), s3_client(), s3_bucket())
    except Exception:  # missing AWS settings: no photos, not a crash at start-up
        return NoImagery()
