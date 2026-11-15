"""The same field must decide the same way from the CSV and from ClickHouse (review, Critical 3).

This is the test that would have caught the 26-versus-27 disagreement on its own. My sweep read the CSV and
counted a `partial` indicator as known; BE's endpoint read ClickHouse and did not, so one field came out
differently and nobody noticed until he said so in a message.

Skips when ClickHouse is unreachable, so `make check` stays green without credentials. It is not a
substitute for the unit tests: it checks that two *sources* of the same data produce the same decision, not
that the decision is right.

Run from the repository root:  uv run pytest engine/tests/test_source_consistency.py -q
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from engine import sweep
from engine.decision import assess
from engine.rules import strategy_rules as rules

REPO_ROOT = Path(__file__).resolve().parents[2]
INDICATORS_CSV = REPO_ROOT / "data" / "out" / "indicators" / "field_indicators.csv"
FIELDS = REPO_ROOT / "data" / "fields" / "fields.geojson"

# One field per crop class, so the comparison covers in-domain and every out-of-domain shape.
SAMPLE_FIELDS = ("primary-001", "test-022", "test-027", "test-033", "test-041")


def _connection():
    try:
        from engine.load_test_set import client

        connection = client()
        connection.query("SELECT 1")
    except Exception as error:
        pytest.skip(f"no usable ClickHouse connection: {error}")
    return connection


@pytest.fixture(scope="module")
def from_csv() -> pd.DataFrame:
    if not INDICATORS_CSV.exists():
        pytest.skip(f"no indicator CSV at {INDICATORS_CSV}; run transform.indicators.runner")
    return pd.read_csv(INDICATORS_CSV)


@pytest.fixture(scope="module")
def from_clickhouse() -> pd.DataFrame:
    connection = _connection()
    frame = connection.query_df(
        "SELECT field_id, indicator_id, category, value, unit, status, "
        "window_start, window_end, valid_obs, unknown_reason "
        # field_indicators is the DE's table and carries load_id, not loaded_at; the newest load wins.
        "FROM field_indicators WHERE load_id = "
        "(SELECT max(load_id) FROM field_indicators)"
    )
    if frame.empty:
        pytest.skip("field_indicators is empty")
    return frame


@pytest.fixture(scope="module")
def fields() -> list[dict]:
    return json.loads(FIELDS.read_text(encoding="utf-8"))["features"]


def _decisions(indicators: pd.DataFrame, fields: list[dict]) -> dict[tuple[str, str], str]:
    wanted = [f for f in fields if f["properties"]["field_id"] in SAMPLE_FIELDS]
    profiles = sweep.build_profiles(indicators, wanted)
    return {
        (profile.field_id, name): assess(profile, constraints).outcome
        for profile in profiles
        for name, constraints in sweep.SCENARIOS.items()
    }


def test_both_sources_hold_the_same_indicator_rows(from_csv, from_clickhouse):
    assert len(from_clickhouse) == len(from_csv), (
        "ClickHouse and the CSV disagree on row count; one of them is from a different run"
    )
    assert set(from_clickhouse["indicator_id"]) == set(from_csv["indicator_id"])


def test_the_same_field_decides_the_same_way_from_either_source(from_csv, from_clickhouse, fields):
    csv_decisions = _decisions(from_csv, fields)
    db_decisions = _decisions(from_clickhouse, fields)
    assert csv_decisions, "no sample field was found in the field file"

    differences = {
        key: (csv_decisions[key], db_decisions.get(key))
        for key in csv_decisions
        if csv_decisions[key] != db_decisions.get(key)
    }
    assert not differences, (
        "the same field decides differently depending on where the indicators were read from: "
        + "; ".join(
            f"{field} under {scenario}: CSV says {csv}, ClickHouse says {db}"
            for (field, scenario), (csv, db) in differences.items()
        )
    )


def test_partial_indicators_are_treated_the_same_either_way(from_csv, from_clickhouse):
    """The specific disagreement that started this: `partial` counted as known in one path only.

    Only a partial on a *required* indicator can change a decision, so this looks for one of those. Fields
    whose partial is on, say, sand content are unaffected by design.
    """
    required_keys = {"gdd", "precipitation_total", "frost_free_days", "om_r_0_30cm"}
    for frame, label in ((from_csv, "csv"), (from_clickhouse, "clickhouse")):
        partial = frame[(frame["status"] == "partial") & (frame["indicator_id"].isin(required_keys))]
        if partial.empty:
            pytest.skip(f"{label}: no field has a partial required indicator")
        field_id = partial.iloc[0]["field_id"]
        statuses = sweep._indicator_statuses(frame, field_id)
        assert "unknown" in statuses.values(), (
            f"{label}: {field_id} has a partial required indicator, so it must not read as fully known"
        )


def test_the_loaded_rules_version_matches_the_code(from_clickhouse):
    connection = _connection()
    loaded = connection.query(
        "SELECT rules_version FROM engine_rules ORDER BY loaded_at DESC LIMIT 1"
    ).result_rows
    if not loaded:
        pytest.skip("engine_rules is empty")
    assert loaded[0][0] == rules.RULES_VERSION, (
        f"ClickHouse holds rules {loaded[0][0]} but this checkout is {rules.RULES_VERSION}; "
        "the audit and the endpoint would describe different rules"
    )
