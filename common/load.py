"""Idempotent load into a core table: validate, stage, assert, then swap whole partitions.

    result = load(client, "fields", frame)

Order of operations (specs/tech-stack.md, Data integrity, ClickHouse):
  1. Pandera validation of the frame, before anything touches the database.
  2. A staging table with the live table's structure, one batch insert.
  3. Post-load assertions on staging. Any problem raises LoadRejected; the live table is untouched.
  4. REPLACE PARTITION per partition present in staging, then the staging table is dropped.

A partition is the unit a reload replaces: the frame must hold every row for each partition it
touches (all of one source for data_sources, all of one code_version for indicator_lineage, all
fields for fields). Partitions the frame does not mention are left alone.
"""

import hashlib
import subprocess
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from common.assertions import check_table
from common.schemas import TABLES

REPO_ROOT = Path(__file__).resolve().parent.parent


class LoadRejected(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class LoadResult:
    """The run record for the run manifest."""

    load_id: str
    table: str
    rows: int
    partitions: tuple[str, ...]
    git_sha: str
    input_sha256: str
    loaded_at: str


def git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def frame_sha256(frame: pd.DataFrame) -> str:
    """Content hash of the input, independent of row order, recorded as the load's input checksum."""
    ordered = frame.sort_values(list(frame.columns)).reset_index(drop=True)
    return hashlib.sha256(ordered.to_csv(index=False).encode()).hexdigest()


def load(client, table: str, frame: pd.DataFrame, load_id: str | None = None) -> LoadResult:
    if table not in TABLES:
        raise KeyError(f"unknown table {table!r}; known: {sorted(TABLES)}")
    spec = TABLES[table]
    valid = spec.schema.validate(frame)  # raises pandera SchemaError(s) before any database call
    load_id = load_id or uuid.uuid4().hex
    staged = valid.assign(load_id=load_id)
    staging = f"{table}__staging"

    client.command(f"DROP TABLE IF EXISTS `{staging}`")
    client.command(f"CREATE TABLE `{staging}` AS `{table}`")
    try:
        client.insert_df(staging, staged)
        problems = check_table(client, table, expected_rows=len(staged), target=staging)
        if problems:
            raise LoadRejected(problems)
        rows = client.query(
            f"SELECT DISTINCT partition_id FROM system.parts "
            f"WHERE database = currentDatabase() AND table = '{staging}' AND active ORDER BY 1"
        ).result_rows
        partitions = tuple(row[0] for row in rows)
        for partition_id in partitions:
            client.command(f"ALTER TABLE `{table}` REPLACE PARTITION ID '{partition_id}' FROM `{staging}`")
    finally:
        client.command(f"DROP TABLE IF EXISTS `{staging}`")

    return LoadResult(
        load_id=load_id,
        table=table,
        rows=len(staged),
        partitions=partitions,
        git_sha=git_sha(),
        input_sha256=frame_sha256(valid),
        loaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
