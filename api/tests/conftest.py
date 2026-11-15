import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.db.repository import FileRepository
from api.main import create_app
from api.settings import Settings


@pytest.fixture(scope="session")
def repository() -> FileRepository:
    """Real committed field data, with no indicator outputs (the state of the repo today)."""
    return FileRepository(indicators_dir=Path("/nonexistent"))


@pytest.fixture()
def client(repository) -> TestClient:
    return TestClient(create_app(Settings(), repository))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def indicator_row(field_id, indicator_id, value, status="available"):
    return {
        "field_id": field_id,
        "indicator_id": indicator_id,
        "category": "x",
        "value": value,
        "unit": "u",
        "status": status,
        "window_start": "2015-04-01",
        "window_end": "2015-11-30",
        "valid_obs": "1",
        "unknown_reason": "",
        "run_id": "t",
    }


def soil_row(field_id, prop, label, share):
    return {
        "field_id": field_id,
        "mukey": "",
        "mu_name": "",
        "share_pct": share,
        "property": prop,
        "value_num": share,
        "value_text": label,
        "unit": "%",
        "indicator_id": prop,
        "run_id": "t",
    }


@pytest.fixture()
def indicator_dir(tmp_path) -> Path:
    """Indicator outputs shaped like DS2's runner writes them, for primary-001 only."""
    f = "primary-001"
    rows = []
    for _ in range(2):  # two seasons
        rows += [
            indicator_row(f, "gdd", "1500"),
            indicator_row(f, "precipitation_total", "600"),
        ]
    rows += [
        indicator_row(f, "frost_free_days", "150"),
        indicator_row(f, "frost_free_days", "160"),
        indicator_row(f, "om_r_0_30cm", "3.1"),
        indicator_row(f, "gdd_season_difference_vs_marsden", "80"),
    ]
    write_csv(tmp_path / "field_indicators.csv", rows)
    write_csv(
        tmp_path / "soil_properties.csv",
        [
            soil_row(f, "drainagecl", "Poorly drained", "70"),
            soil_row(f, "drainagecl", "Somewhat poorly drained", "30"),
            soil_row(f, "hydgrp", "C/D", "100"),
        ],
    )
    return tmp_path
