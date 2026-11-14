"""Idempotent load into a core table: validate, stage, assert, then swap whole partitions.

    result = load(client, "fields", frame)

Order of operations (specs/tech-stack.md, Data integrity, ClickHouse):
  1. Pandera validation of the frame, before anything touches the database.
  2. A staging table with the live table's structure, one batch insert.
  3. Post-load assertions on staging. Any problem raises LoadRejected; the live table is untouched.
  4. REPLACE PARTITION swaps the one partition in staging (a frame spanning several partitions is
     rejected, because several swaps are not atomic), then the staging table is dropped.

A partition is the unit a reload replaces: the frame must hold every row for each partition it
touches (all of one source for data_sources, all of one code_version for indicator_lineage, all
fields for fields). Partitions the frame does not mention are left alone.
"""

import hashlib
import re
import subprocess
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from common.assertions import check_table, orphan_indicators
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
    """HEAD, with `-dirty` when the working tree has uncommitted changes (the code that ran is then
    not the code at that commit)."""
    try:
        def git(*args):
            return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout

        return git("rev-parse", "HEAD").strip() + ("-dirty" if git("status", "--porcelain").strip() else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def frame_sha256(frame: pd.DataFrame) -> str:
    """Content hash of the input, independent of row order, recorded as the load's input checksum.
    It hashes the CSV text of the frame, so it identifies an input within one environment; it is not
    guaranteed stable across pandas versions."""
    ordered = frame.sort_values(list(frame.columns)).reset_index(drop=True)
    return hashlib.sha256(ordered.to_csv(index=False).encode()).hexdigest()


def load(
    client, table: str, frame: pd.DataFrame, load_id: str | None = None, prefix: str = ""
) -> LoadResult:
    if table not in TABLES:
        raise KeyError(f"unknown table {table!r}; known: {sorted(TABLES)}")
    spec = TABLES[table]
    valid = spec.schema.validate(frame)  # raises pandera SchemaError(s) before any database call
    if valid.empty:  # a silent no-op would hide an upstream step that produced nothing
        raise LoadRejected([f"{table}: the frame is empty, nothing to load"])
    load_id = load_id or uuid.uuid4().hex
    if not re.fullmatch(r"\w+", load_id):
        raise ValueError("load_id may only hold letters, digits and underscores")
    staged = valid.assign(load_id=load_id)
    live = f"{prefix}{table}"  # the prefix is only ever used by the live tests
    staging = f"{live}__staging_{load_id}"  # one staging table per load, so two loads cannot collide

    client.command(f"DROP TABLE IF EXISTS `{staging}`")
    client.command(f"CREATE TABLE `{staging}` AS `{live}`")
    try:
        client.insert_df(staging, staged)
        problems = check_table(client, table, expected_rows=len(staged), target=staging)
        if spec.lineage_column:
            problems += orphan_indicators(
                client, staging, spec.lineage_column, lineage=f"{prefix}indicator_lineage"
            )
        if problems:
            raise LoadRejected(problems)
        # _partition_id needs only SELECT on the table (system.parts needs a grant most users lack)
        rows = client.query(f"SELECT DISTINCT _partition_id FROM `{staging}` ORDER BY 1").result_rows
        partitions = tuple(row[0] for row in rows)
        if len(partitions) > 1:  # several swaps would not be atomic: a failure part-way leaves a mix
            raise LoadRejected(
                [f"{table}: the frame spans {len(partitions)} partitions; load one partition per call"]
            )
        for partition_id in partitions:
            client.command(f"ALTER TABLE `{live}` REPLACE PARTITION ID '{partition_id}' FROM `{staging}`")
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
