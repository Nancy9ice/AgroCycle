"""Live checks against the real ClickHouse server, in scratch tables named `scratch_<id>_<table>`.

Skipped when ClickHouse settings are missing, so `make check` stays green for teammates without
access. The scratch tables sit beside the project tables (the project database needs no extra
privilege) and are dropped afterwards; each test asserts none are left.
"""

import uuid

import pandas as pd
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
    assert migrate(client, prefix=p) == [
        "001_core.sql", "002_crop_history.sql", "003_indicators.sql", "004_hls_valid_pixels.sql",
        "006_data_sources.sql",
    ]
    assert migrate(client, prefix=p) == []
    found = client.query(
        f"SELECT name FROM system.tables WHERE database = currentDatabase() AND startsWith(name, '{p}')"
    ).result_rows
    assert {name for (name,) in found} == {
        f"{p}{t}"
        for t in ("data_sources", "indicator_lineage", "fields", "schema_migrations",
                  "crop_class_shares", "crop_history", "crop_rotation",
                  "field_indicators", "soil_properties", "climate_points", "climate_daily",
                  "hls_valid_pixels", "source_links")
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


def test_reloading_one_version_leaves_other_versions_alone(scratch, lineage_frame):
    client, p = scratch
    migrate(client, prefix=p)
    live = f"{p}indicator_lineage"
    v1, v2 = lineage_frame.assign(code_version="v1"), lineage_frame.assign(code_version="v2")
    loader.load(client, "indicator_lineage", v1, prefix=p)
    loader.load(client, "indicator_lineage", v2, prefix=p)
    loader.load(client, "indicator_lineage", v1.iloc[:1], prefix=p)  # v1 shrinks to one row
    assert client.query(f"SELECT count() FROM `{live}` WHERE code_version = 'v1'").result_rows == [(1,)]
    assert client.query(f"SELECT count() FROM `{live}` WHERE code_version = 'v2'").result_rows == [(len(lineage_frame),)]


def test_sources_and_links_load_twice_with_identical_content(scratch, data_sources_frame, source_links_frame):
    client, p = scratch
    migrate(client, prefix=p)
    for table, frame in (("data_sources", data_sources_frame), ("source_links", source_links_frame)):
        loader.load(client, table, frame, prefix=p)
        first = assertions.table_hash(client, f"{p}{table}")
        loader.load(client, table, frame, prefix=p)
        assert assertions.table_hash(client, f"{p}{table}") == first
        assert client.query(f"SELECT count() FROM `{p}{table}`").result_rows == [(len(frame),)]


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
    table = f"{p}probe_indicators"
    client.command(f"CREATE TABLE `{table}` (indicator_id String) ENGINE = MergeTree ORDER BY indicator_id")
    client.insert(table, [["gdd"], ["mystery"]], column_names=["indicator_id"])
    problems = assertions.orphan_indicators(client, table, lineage=f"{p}indicator_lineage")
    assert problems == [f"{table}: indicator 'mystery' has no indicator_lineage row"]


def test_a_frame_spanning_two_partitions_is_rejected_and_nothing_changes(scratch, lineage_frame):
    client, p = scratch
    migrate(client, prefix=p)
    live = f"{p}indicator_lineage"
    loader.load(client, "indicator_lineage", lineage_frame.assign(code_version="v1"), prefix=p)
    before = assertions.table_hash(client, live)
    two = pd.concat([lineage_frame.assign(code_version="v1"), lineage_frame.assign(code_version="v2")], ignore_index=True)
    with pytest.raises(loader.LoadRejected, match="2 partitions"):
        loader.load(client, "indicator_lineage", two, prefix=p)
    assert assertions.table_hash(client, live) == before


def test_the_climate_tables_load_twice_with_identical_content(scratch):
    import json
    from pathlib import Path

    from transform.clean import power

    sample = next((Path(__file__).resolve().parents[2] / "data" / "sample" / "primary-001" / "power").glob("*.json"))
    document = json.loads(sample.read_text())
    document["properties"]["parameter"]["T2M"]["20230103"] = -999.0  # one fill value: a null in a Nullable(Float32)
    points, daily = power.group_cells([power.clean_point(document, "primary-001")])
    client, p = scratch
    migrate(client, prefix=p)
    for table, frame in (("climate_points", points), ("climate_daily", daily)):
        live = f"{p}{table}"
        first = loader.load(client, table, frame, prefix=p)
        hash_one = assertions.table_hash(client, live)
        second = loader.load(client, table, frame, prefix=p)
        assert assertions.table_hash(client, live) == hash_one and first.input_sha256 == second.input_sha256
        assert client.query(f"SELECT count() FROM `{live}`").result_rows == [(len(frame),)]
    filled = client.query(
        f"SELECT count(), countIf(isNull(value)) FROM `{p}climate_daily` WHERE qc_flag = 'fill'"
    ).result_rows
    assert filled == [(1, 1)]  # the fill value is stored as null, flagged


def _ds2_files(directory, complete=True):
    """DS2-shaped CSVs: nulls in every nullable column, blank text, two seasons of one indicator."""
    import pandas as pd

    from transform.indicators import runner

    columns = ["field_id", "indicator_id", "category", "value", "unit", "status", "window_start", "window_end",
               "valid_obs", "unknown_reason", "run_id"]
    rows = [
        ["primary-001", "gdd", "climate", 1800.5, "degree-days C", "available", "2023-04-01", "2023-11-30", 244, "", "r1"],
        ["primary-001", "gdd", "climate", "", "degree-days C", "unknown", "2024-04-01", "2024-11-30", 100, "too few days", "r1"],
        ["primary-001", "slope_r", "soil", 3.2, "%", "available", "", "", "", "", "r1"],
    ]
    soil = [
        ["primary-001", "2345", "Canisteo", 30.5, "map_unit_share", 30.5, "", "% of field area", "map_unit_share", "r1"],
        ["primary-001", "", "", 60.0, "drainagecl", 60.0, "Poorly drained", "% of field area", "drainagecl", "r1"],
    ]
    pd.DataFrame(rows, columns=columns).to_csv(directory / "field_indicators.csv", index=False)
    pd.DataFrame(soil, columns=["field_id", "mukey", "mu_name", "share_pct", "property", "value_num", "value_text",
                                "unit", "indicator_id", "run_id"]).to_csv(directory / "soil_properties.csv", index=False)
    lineage = runner.lineage_rows("r1")
    if complete:
        lineage.append({**lineage[0], "indicator_id": "map_unit_share", "label": "map unit share"})
    pd.DataFrame(lineage).to_csv(directory / "indicator_lineage.csv", index=False)


def test_ds2_shaped_files_load_with_their_nulls_and_the_lineage_check(scratch, tmp_path):
    from transform.indicators import load as indicator_load

    client, p = scratch
    migrate(client, prefix=p)
    _ds2_files(tmp_path)
    frames = indicator_load.read_frames(tmp_path)
    for name in indicator_load.FILES:
        result = loader.load(client, name, frames[name], prefix=p)
        assert result.rows == len(frames[name])
    got = client.query(
        f"SELECT indicator_id, value, status, window_start, valid_obs, unknown_reason FROM `{p}field_indicators` "
        f"ORDER BY indicator_id, window_start"
    ).result_rows
    assert got[0][1:3] == (1800.5, "available") and got[1][1] is None and got[1][2] == "unknown"
    assert got[1][5] == "too few days" and got[0][5] is None  # a blank reason is null, not empty text
    assert got[2][0] == "slope_r" and got[2][3] is None and got[2][4] is None  # a soil indicator has no window
    soil = client.query(f"SELECT mukey, value_text FROM `{p}soil_properties` ORDER BY mukey").result_rows
    assert soil == [("", "Poorly drained"), ("2345", None)]
    before = assertions.table_hash(client, f"{p}field_indicators")
    loader.load(client, "field_indicators", frames["field_indicators"], prefix=p)
    assert assertions.table_hash(client, f"{p}field_indicators") == before


def test_an_indicator_with_no_lineage_row_is_refused_by_the_loader_itself(scratch, tmp_path):
    from transform.indicators import load as indicator_load

    client, p = scratch
    migrate(client, prefix=p)
    _ds2_files(tmp_path, complete=False)  # the lineage lacks map_unit_share
    frames = indicator_load.read_frames(tmp_path)
    loader.load(client, "indicator_lineage", frames["indicator_lineage"], prefix=p)
    with pytest.raises(loader.LoadRejected, match="map_unit_share"):
        loader.load(client, "soil_properties", frames["soil_properties"], prefix=p)
    assert client.query(f"SELECT count() FROM `{p}soil_properties`").result_rows == [(0,)]

def test_the_hls_counts_load_twice_with_identical_content_and_keep_their_enum_and_dates(scratch, hls_frame):
    client, p = scratch
    migrate(client, prefix=p)
    live = f"{p}hls_valid_pixels"
    first = loader.load(client, "hls_valid_pixels", hls_frame, prefix=p)
    hash_one = assertions.table_hash(client, live)
    second = loader.load(client, "hls_valid_pixels", hls_frame, prefix=p)
    assert assertions.table_hash(client, live) == hash_one and first.input_sha256 == second.input_sha256
    rows = client.query(
        f"SELECT sensor, acquired, status, valid_pixels, valid_share FROM `{live}` ORDER BY acquired"
    ).result_rows
    assert [r[2] for r in rows] == ["observed", "observed", "no_data"] and rows[2][3] == 0
    assert str(rows[0][1]) == "2023-04-05" and rows[0][4] == pytest.approx(384 / 484, rel=1e-6)
    assert client.query(f"SELECT count() FROM `{live}`").result_rows == [(3,)]
