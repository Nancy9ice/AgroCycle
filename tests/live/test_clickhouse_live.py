"""Live checks against the real ClickHouse server, in a throwaway scratch database.

Skipped when ClickHouse settings are missing or the user cannot create a database, so `make check`
stays green for teammates without access. The scratch database is dropped afterwards.
"""

import uuid

import pytest
from clickhouse_connect.driver.exceptions import ClickHouseError

from common import assertions
from common import load as loader
from common.migrate import migrate


@pytest.fixture
def scratch():
    from common.config import clickhouse_client

    try:
        admin = clickhouse_client()
    except RuntimeError as error:  # missing settings
        pytest.skip(str(error))
    name = f"scratch_{uuid.uuid4().hex[:10]}"
    try:
        admin.command(f"CREATE DATABASE `{name}`")
    except ClickHouseError as error:  # no permission to create databases
        pytest.skip(f"cannot create a scratch database: {error}")
    try:
        yield clickhouse_client(database=name), name
    finally:
        admin.command(f"DROP DATABASE IF EXISTS `{name}`")
        left = admin.query(f"SELECT count() FROM system.databases WHERE name = '{name}'").result_rows
        assert left == [(0,)], "scratch database was not removed"


def test_migrate_creates_tables_and_is_rerunnable(scratch):
    client, name = scratch
    assert "001_core.sql" in migrate(client)
    assert migrate(client) == []
    tables = {r[0] for r in client.query(f"SELECT name FROM system.tables WHERE database = '{name}'").result_rows}
    assert {"data_sources", "indicator_lineage", "fields", "schema_migrations"} <= tables


def test_loading_twice_gives_identical_hashes_and_no_duplicates(scratch, fields_frame, lineage_frame):
    client, _ = scratch
    migrate(client)
    for table, frame in (("fields", fields_frame), ("indicator_lineage", lineage_frame)):
        first = loader.load(client, table, frame)
        hash_one = assertions.table_hash(client, table)
        second = loader.load(client, table, frame)
        assert assertions.table_hash(client, table) == hash_one
        assert client.query(f"SELECT count() FROM {table}").result_rows == [(len(frame),)]
        assert first.load_id != second.load_id
        assert first.input_sha256 == second.input_sha256
        assert client.query(f"SELECT uniqExact(load_id) FROM {table}").result_rows == [(1,)]  # only the last run


def test_reloading_one_source_leaves_other_sources_alone(scratch, data_sources_frame):
    client, _ = scratch
    migrate(client)
    power = data_sources_frame.assign(source_id="power", s3_key=["raw/power/a", "raw/power/b"])
    loader.load(client, "data_sources", data_sources_frame)
    loader.load(client, "data_sources", power)
    before = client.query("SELECT count() FROM data_sources WHERE source_id = 'power'").result_rows
    loader.load(client, "data_sources", data_sources_frame.iloc[:1])  # cdl shrinks to one file
    assert client.query("SELECT count() FROM data_sources WHERE source_id = 'cdl'").result_rows == [(1,)]
    assert client.query("SELECT count() FROM data_sources WHERE source_id = 'power'").result_rows == before


def test_rejected_load_leaves_the_live_table_unchanged(scratch, fields_frame, monkeypatch):
    client, _ = scratch
    migrate(client)
    loader.load(client, "fields", fields_frame)
    before = assertions.table_hash(client, "fields")
    monkeypatch.setattr(loader, "check_table", lambda *a, **k: ["forced failure"])
    with pytest.raises(loader.LoadRejected):
        loader.load(client, "fields", fields_frame.assign(county="Boone"))
    assert assertions.table_hash(client, "fields") == before
    leftovers = client.query("SELECT count() FROM system.tables WHERE name LIKE '%__staging'").result_rows
    assert leftovers == [(0,)]


def test_indicator_without_lineage_is_flagged(scratch, lineage_frame):
    client, _ = scratch
    migrate(client)
    loader.load(client, "indicator_lineage", lineage_frame)  # gdd has a lineage row
    client.command("CREATE TABLE field_indicators (indicator_id String) ENGINE = MergeTree ORDER BY indicator_id")
    client.insert("field_indicators", [["gdd"], ["mystery"]], column_names=["indicator_id"])
    problems = assertions.orphan_indicators(client, "field_indicators")
    assert problems == ["field_indicators: indicator 'mystery' has no indicator_lineage row"]
