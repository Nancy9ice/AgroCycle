"""Live checks against the real ClickHouse server, in scratch tables named `scratch_<id>_<table>`.

Skipped when ClickHouse settings are missing, so `make check` stays green for teammates without
access. The scratch tables sit beside the project tables (the project database needs no extra
privilege) and are dropped afterwards; each test asserts none are left.
"""

import uuid

import pytest

from common import assertions
from common import load as loader
from common.migrate import migrate


@pytest.fixture
def scratch():
    from common.config import clickhouse_client

    try:
        client = clickhouse_client()
    except Exception as error:  # noqa: BLE001  missing settings, no network, bad login: none should fail make check
        pytest.skip(f"no usable ClickHouse connection: {error}")
    prefix = f"scratch_{uuid.uuid4().hex[:8]}_"
    where = f"database = currentDatabase() AND startsWith(name, '{prefix}')"
    try:
        yield client, prefix
    finally:
        for (name,) in client.query(f"SELECT name FROM system.tables WHERE {where}").result_rows:
            client.command(f"DROP TABLE IF EXISTS `{name}`")
        assert client.query(f"SELECT count() FROM system.tables WHERE {where}").result_rows == [(0,)]


def test_migrate_creates_tables_and_is_rerunnable(scratch):
    client, p = scratch
    assert migrate(client, prefix=p) == ["001_core.sql", "002_crop_history.sql"]
    assert migrate(client, prefix=p) == []
    found = client.query(
        f"SELECT name FROM system.tables WHERE database = currentDatabase() AND startsWith(name, '{p}')"
    ).result_rows
    assert {name for (name,) in found} == {
        f"{p}{t}"
        for t in ("data_sources", "indicator_lineage", "fields", "schema_migrations",
                  "crop_class_shares", "crop_history", "crop_rotation")
    }


def test_loading_twice_gives_identical_hashes_and_no_duplicates(
    scratch, fields_frame, lineage_frame, crop_shares_frame, crop_history_frame, crop_rotation_frame
):
    client, p = scratch
    migrate(client, prefix=p)
    tables = (
        ("fields", fields_frame),
        ("indicator_lineage", lineage_frame),
        ("crop_class_shares", crop_shares_frame),
        ("crop_history", crop_history_frame),
        ("crop_rotation", crop_rotation_frame),
    )
    for table, frame in tables:
        live = f"{p}{table}"
        first = loader.load(client, table, frame, prefix=p)
        hash_one = assertions.table_hash(client, live)
        second = loader.load(client, table, frame, prefix=p)
        assert assertions.table_hash(client, live) == hash_one
        assert client.query(f"SELECT count() FROM `{live}`").result_rows == [(len(frame),)]
        assert first.load_id != second.load_id
        assert first.input_sha256 == second.input_sha256
        # only the last run's rows remain
        assert client.query(f"SELECT uniqExact(load_id) FROM `{live}`").result_rows == [(1,)]
        print(f"{table}: table hash {hash_one} after both loads")


def test_reloading_one_source_leaves_other_sources_alone(scratch, data_sources_frame):
    client, p = scratch
    migrate(client, prefix=p)
    live = f"{p}data_sources"
    power = data_sources_frame.assign(source_id="power", s3_key=["raw/power/a", "raw/power/b"])
    loader.load(client, "data_sources", data_sources_frame, prefix=p)
    loader.load(client, "data_sources", power, prefix=p)
    loader.load(client, "data_sources", data_sources_frame.iloc[:1], prefix=p)  # cdl shrinks to one file
    assert client.query(f"SELECT count() FROM `{live}` WHERE source_id = 'cdl'").result_rows == [(1,)]
    assert client.query(f"SELECT count() FROM `{live}` WHERE source_id = 'power'").result_rows == [(2,)]


def test_rejected_load_leaves_the_live_table_unchanged(scratch, fields_frame, monkeypatch):
    client, p = scratch
    migrate(client, prefix=p)
    live = f"{p}fields"
    loader.load(client, "fields", fields_frame, prefix=p)
    before = assertions.table_hash(client, live)
    monkeypatch.setattr(loader, "check_table", lambda *a, **k: ["forced failure"])
    with pytest.raises(loader.LoadRejected):
        loader.load(client, "fields", fields_frame.assign(county="Boone"), prefix=p)
    assert assertions.table_hash(client, live) == before
    leftovers = client.query(
        f"SELECT count() FROM system.tables WHERE database = currentDatabase() "
        f"AND startsWith(name, '{p}') AND name LIKE '%__staging%'"
    ).result_rows
    assert leftovers == [(0,)]


def test_a_real_assertion_failure_is_caught(scratch, fields_frame):
    """No monkeypatching: put an empty text key straight into a probe table, as if Pandera had been
    bypassed, and check the assertion reports it."""
    client, p = scratch
    migrate(client, prefix=p)
    live = f"{p}fields"
    client.command(f"CREATE TABLE `{live}__probe` AS `{live}`")
    bad = fields_frame.assign(load_id="x")
    bad.loc[0, "field_id"] = ""
    client.insert_df(f"{live}__probe", bad)
    problems = assertions.check_table(client, "fields", expected_rows=2, target=f"{live}__probe")
    assert any("empty field_id" in problem for problem in problems)


def test_indicator_without_lineage_is_flagged(scratch, lineage_frame):
    client, p = scratch
    migrate(client, prefix=p)
    loader.load(client, "indicator_lineage", lineage_frame, prefix=p)  # gdd has a lineage row
    table = f"{p}field_indicators"
    client.command(f"CREATE TABLE `{table}` (indicator_id String) ENGINE = MergeTree ORDER BY indicator_id")
    client.insert(table, [["gdd"], ["mystery"]], column_names=["indicator_id"])
    problems = assertions.orphan_indicators(client, table, lineage=f"{p}indicator_lineage")
    assert problems == [f"{table}: indicator 'mystery' has no indicator_lineage row"]


def test_a_frame_spanning_two_partitions_is_rejected_and_nothing_changes(scratch, data_sources_frame):
    client, p = scratch
    migrate(client, prefix=p)
    live = f"{p}data_sources"
    loader.load(client, "data_sources", data_sources_frame, prefix=p)
    before = assertions.table_hash(client, live)
    two = data_sources_frame.assign(source_id=["cdl", "power"], s3_key=["raw/cdl/a", "raw/power/a"])
    with pytest.raises(loader.LoadRejected, match="2 partitions"):
        loader.load(client, "data_sources", two, prefix=p)
    assert assertions.table_hash(client, live) == before
