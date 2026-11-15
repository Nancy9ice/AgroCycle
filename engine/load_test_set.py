"""Load the engine test-set audit into ClickHouse (AgroCycle, DS2, roadmap Phase 14).

Creates `engine_test_set` if it is absent and loads the rows `engine.sweep` wrote, so BE's
`GET /validation/test-set` has something to query. One row per field per constraint scenario.

Re-running the same run_id replaces its rows rather than duplicating them; earlier runs are left in
place, so the table keeps its history. Readers must pick the newest run by `loaded_at`, not by
`max(run_id)`: the run id is random hex and does not sort chronologically.

Usage from the repository root:

    uv run python -m engine.load_test_set            # dry run: says what it would do
    uv run python -m engine.load_test_set --yes      # create if needed, then load
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import clickhouse_connect
import pandas as pd
from dotenv import load_dotenv

from engine import expected

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "data" / "out" / "validation" / "engine_test_set.csv"
TABLE = "engine_test_set"

DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    field_id                String,
    scenario                LowCardinality(String),
    crop_history_summary    String,
    outcome                 Enum8('strategy_worth_exploring' = 1,
                                  'qualified_comparison' = 2,
                                  'abstention' = 3),
    outcome_reason          String,
    strategy_a_feasibility  LowCardinality(String),
    strategy_b_feasibility  LowCardinality(String),
    strategy_c_feasibility  LowCardinality(String),
    outcomes_in_domain      UInt8,
    outcomes_qualified      UInt8,
    outcomes_abstained      UInt8,
    outcomes_out_of_domain  UInt8,
    outcomes_not_assessed   UInt8,
    rules_fired             String,
    unknowns                String,
    rules_version           LowCardinality(String),
    run_id                  String,
    loaded_at               DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree
ORDER BY (field_id, scenario, run_id)
"""


def client():
    """Connect using the project settings, accepting the docker-compose names as aliases.

    `.env` currently carries CLICKHOUSE_HTTP_PORT and CLICKHOUSE_DB (the names the compose file sets)
    while `common.config` expects CLICKHOUSE_PORT and CLICKHOUSE_DATABASE. Accepting both here means
    this runs either way; the duplication belongs in `.env`, not in more code.
    """
    load_dotenv(REPO_ROOT / ".env")
    port = os.environ.get("CLICKHOUSE_PORT") or os.environ.get("CLICKHOUSE_HTTP_PORT")
    database = os.environ.get("CLICKHOUSE_DATABASE") or os.environ.get("CLICKHOUSE_DB")
    missing = [
        name
        for name, value in (
            ("CLICKHOUSE_HOST", os.environ.get("CLICKHOUSE_HOST")),
            ("CLICKHOUSE_PORT or CLICKHOUSE_HTTP_PORT", port),
            ("CLICKHOUSE_DATABASE or CLICKHOUSE_DB", database),
            ("CLICKHOUSE_USER", os.environ.get("CLICKHOUSE_USER")),
        )
        if not value
    ]
    if missing:
        raise RuntimeError("missing setting(s): " + ", ".join(missing))
    return clickhouse_connect.get_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(port),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        database=database,
        secure=os.environ.get("CLICKHOUSE_SECURE", "true").lower() == "true",
    )


EXPECTED_DDL = """
CREATE TABLE IF NOT EXISTS engine_expected_outcomes (
    case_id          String,
    field_id         String,
    scenario         LowCardinality(String),
    expected_outcome LowCardinality(String),
    expected_reason  String,
    review_state     LowCardinality(String),
    reviewed_by      String,
    source           String,
    loaded_at        DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree ORDER BY case_id
"""

ADDED_COLUMNS = (
    ("expected_outcome", "String"),
    ("expected_reason", "String"),
    ("expected_review_state", "LowCardinality(String)"),
)


def _attach_expectations(frame: pd.DataFrame) -> pd.DataFrame:
    """Fill the expectation columns where a matrix case names that field and scenario, else leave blank."""
    frame = frame.copy()
    matches = [
        expected.expectation_for(row.field_id, row.scenario) for row in frame.itertuples()
    ]
    frame["expected_outcome"] = [m["expected_outcome"] if m else "" for m in matches]
    frame["expected_reason"] = [m["expected_reason"] if m else "" for m in matches]
    frame["expected_review_state"] = [m["review_state"] if m else "" for m in matches]
    return frame


def load(connection, frame: pd.DataFrame) -> dict:
    connection.command(DDL)
    for column, kind in ADDED_COLUMNS:
        connection.command(f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS {column} {kind}")
    connection.command(EXPECTED_DDL)
    connection.command("TRUNCATE TABLE engine_expected_outcomes")
    rows = expected.expected_rows()
    columns = list(rows[0])
    connection.insert(
        "engine_expected_outcomes",
        [[row[c] for c in columns] for row in rows],
        column_names=columns,
    )
    frame = _attach_expectations(frame)
    run_ids = sorted(frame["run_id"].unique())
    for run_id in run_ids:
        connection.command(
            f"ALTER TABLE {TABLE} DELETE WHERE run_id = %(run_id)s", parameters={"run_id": run_id}
        )
    columns = [column for column in frame.columns]
    connection.insert(TABLE, frame[columns].values.tolist(), column_names=columns)
    total = connection.query(f"SELECT count() FROM {TABLE}").result_rows[0][0]
    return {"run_ids": run_ids, "inserted": len(frame), "table_rows": total}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--yes", action="store_true", help="actually create and load")
    args = parser.parse_args(argv)

    if not args.csv.exists():
        print(f"no rows at {args.csv}; run: uv run python -m engine.sweep")
        return 1
    frame = pd.read_csv(args.csv)
    print(f"{len(frame)} rows, run_id(s) {sorted(frame['run_id'].unique())}")
    print(f"  {frame['field_id'].nunique()} fields x {frame['scenario'].nunique()} scenarios")

    if not args.yes:
        print(f"\ndry run; nothing written. Re-run with --yes to create {TABLE} and load.")
        return 0

    connection = client()
    result = load(connection, frame)
    print(f"loaded {result['inserted']} rows; {TABLE} now holds {result['table_rows']}")
    # max(run_id) would be the lexicographic maximum of a random hex id, not the newest run.
    for row in connection.query(
        f"SELECT scenario, outcome, count() FROM {TABLE} "
        f"WHERE run_id = (SELECT run_id FROM {TABLE} ORDER BY loaded_at DESC LIMIT 1) "
        "GROUP BY scenario, outcome ORDER BY scenario, outcome"
    ).result_rows:
        print(f"  {row[0]:<24}{row[1]:<26}{row[2]:>4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
