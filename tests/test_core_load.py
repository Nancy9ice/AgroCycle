import pandera.errors
import pytest

from common import assertions
from common.load import LoadRejected, frame_sha256, load
from common.migrate import migrate, split_statements, with_prefix
from tests.conftest import FakeClient

GOOD = [
    ("count() FROM `fields__staging_L1` WHERE", [(0,)]),
    ("count() - uniqExact", [(0,)]),
    ("count() FROM `fields__staging_L1`", [(2,)]),
    ("_partition_id", [("all",)]),
]


def test_load_order_is_stage_assert_swap_drop(fields_frame):
    client = FakeClient(GOOD)
    result = load(client, "fields", fields_frame, load_id="L1")
    statements = client.statements()
    create = next(i for i, s in enumerate(statements) if s.startswith("CREATE TABLE `fields__staging_L1`"))
    insert = client.calls.index(("insert_df", "fields__staging_L1"))
    swap = next(i for i, s in enumerate(statements) if "REPLACE PARTITION ID 'all'" in s)
    drop = max(i for i, s in enumerate(statements) if s.startswith("DROP TABLE IF EXISTS `fields__staging_L1`"))
    assert create < insert < swap < drop == len(statements) - 1
    assert result.rows == 2 and result.partitions == ("all",) and result.load_id == "L1"
    assert (client.inserted["fields__staging_L1"]["load_id"] == "L1").all()


def test_invalid_frame_never_reaches_the_database(fields_frame):
    client = FakeClient(GOOD)
    fields_frame.loc[0, "role"] = "boss"
    with pytest.raises(pandera.errors.SchemaError):
        load(client, "fields", fields_frame, load_id="L1")
    assert client.calls == []


def test_failed_assertion_aborts_before_the_swap_and_drops_staging(fields_frame):
    client = FakeClient([("count() - uniqExact", [(1,)]), *GOOD])
    with pytest.raises(LoadRejected) as caught:
        load(client, "fields", fields_frame, load_id="L1")
    assert "duplicate" in str(caught.value)
    assert not any("REPLACE PARTITION" in s for s in client.statements())
    assert client.statements()[-1].startswith("DROP TABLE IF EXISTS `fields__staging_L1`")


def test_row_count_mismatch_is_rejected(fields_frame):
    client = FakeClient([("count() FROM `fields__staging_L1`", [(1,)]), *GOOD[:3]])
    with pytest.raises(LoadRejected, match="expected 2 rows, found 1"):
        load(client, "fields", fields_frame, load_id="L1")


def test_a_frame_spanning_several_partitions_is_rejected_before_any_swap(data_sources_frame):
    client = FakeClient([("_partition_id", [("p1",), ("p2",)]), ("WHERE `", [(0,)]), ("uniqExact", [(0,)]),
                         ("count() FROM `data_sources__staging_L1`", [(2,)])])
    with pytest.raises(LoadRejected, match="2 partitions"):
        load(client, "data_sources", data_sources_frame, load_id="L1")
    assert not any("REPLACE PARTITION" in x for x in client.statements())
    assert client.statements()[-1].startswith("DROP TABLE IF EXISTS `data_sources__staging_L1`")


def test_unknown_table_is_refused(fields_frame):
    with pytest.raises(KeyError):
        load(FakeClient(), "users; DROP TABLE fields", fields_frame)


def test_input_checksum_ignores_row_order(fields_frame):
    assert frame_sha256(fields_frame) == frame_sha256(fields_frame.iloc[::-1])
    assert frame_sha256(fields_frame) != frame_sha256(fields_frame.assign(county="Boone"))


def test_orphan_indicator_is_flagged():
    client = FakeClient([("NOT IN", [("mystery",)])])
    problems = assertions.orphan_indicators(client, "field_indicators")
    assert problems == ["field_indicators: indicator 'mystery' has no indicator_lineage row"]
    assert assertions.orphan_indicators(FakeClient([("NOT IN", [])]), "field_indicators") == []


def test_table_hash_ignores_load_id():
    client = FakeClient()
    assertions.table_hash(client, "fields")
    assert "* EXCEPT (load_id)" in client.statements()[0]


def test_split_statements_drops_comments():
    sql = "-- note; with semicolon\nCREATE TABLE a (x Int8) ENGINE = MergeTree ORDER BY x;\n\n-- more\nSELECT 1;"
    assert split_statements(sql) == ["CREATE TABLE a (x Int8) ENGINE = MergeTree ORDER BY x", "SELECT 1"]


def test_migrate_applies_once_and_refuses_edited_files(tmp_path):
    (tmp_path / "001_a.sql").write_text("CREATE TABLE IF NOT EXISTS a (x Int8) ENGINE = MergeTree ORDER BY x;")
    client = FakeClient([("FROM schema_migrations", [])])
    assert migrate(client, tmp_path) == ["001_a.sql"]
    assert ("insert", "schema_migrations") in client.calls

    import hashlib

    checksum = hashlib.sha256((tmp_path / "001_a.sql").read_bytes()).hexdigest()
    again = FakeClient([("FROM schema_migrations", [("001_a.sql", checksum)])])
    assert migrate(again, tmp_path) == []
    assert not any("CREATE TABLE IF NOT EXISTS a" in s for s in again.statements())

    (tmp_path / "001_a.sql").write_text("CREATE TABLE IF NOT EXISTS a (y Int8) ENGINE = MergeTree ORDER BY y;")
    with pytest.raises(RuntimeError, match="edited"):
        migrate(again, tmp_path)


def test_migration_file_names_are_checked(tmp_path):
    (tmp_path / "core.sql").write_text("SELECT 1;")
    with pytest.raises(ValueError):
        migrate(FakeClient(), tmp_path)


def test_prefix_renames_tables_in_migrations_and_loads(fields_frame):
    from common.migrate import with_prefix

    assert with_prefix("CREATE TABLE IF NOT EXISTS fields (x Int8) ENGINE = MergeTree", "s_") == (
        "CREATE TABLE IF NOT EXISTS s_fields (x Int8) ENGINE = MergeTree"
    )
    client = FakeClient([("_partition_id", [("all",)]), ("WHERE", [(0,)]), ("uniqExact", [(0,)]),
                         ("count()", [(2,)])])
    load(client, "fields", fields_frame, load_id="L1", prefix="s_")
    statements = client.statements()
    assert "CREATE TABLE `s_fields__staging_L1` AS `s_fields`" in statements
    assert any(s.startswith("ALTER TABLE `s_fields` REPLACE PARTITION") for s in statements)
    assert not any("`fields`" in s for s in statements)


def test_an_empty_frame_is_rejected_not_silently_loaded(fields_frame):
    client = FakeClient(GOOD)
    with pytest.raises(LoadRejected, match="empty"):
        load(client, "fields", fields_frame.iloc[0:0])
    assert client.calls == []


def test_each_load_has_its_own_staging_table_and_a_safe_load_id(fields_frame):
    any_staging = [("_partition_id", [("all",)]), ("WHERE `", [(0,)]), ("uniqExact", [(0,)]), ("count()", [(2,)])]
    a, b = FakeClient(any_staging), FakeClient(any_staging)
    load(a, "fields", fields_frame, load_id="A")
    load(b, "fields", fields_frame, load_id="B")
    assert "CREATE TABLE `fields__staging_A` AS `fields`" in a.statements()
    assert "CREATE TABLE `fields__staging_B` AS `fields`" in b.statements()
    with pytest.raises(ValueError):
        load(FakeClient(), "fields", fields_frame, load_id="x`; DROP TABLE fields; --")


def test_a_table_with_a_lineage_column_has_its_orphans_checked_before_the_swap(fields_frame, monkeypatch):
    from dataclasses import replace

    from common import load as loader

    monkeypatch.setitem(loader.TABLES, "fields", replace(loader.TABLES["fields"], lineage_column="field_id"))
    client = FakeClient([("NOT IN", [("ghost",)]), *GOOD])
    with pytest.raises(LoadRejected, match="ghost"):
        load(client, "fields", fields_frame, load_id="L1")
    assert not any("REPLACE PARTITION" in x for x in client.statements())


def test_split_statements_handles_semicolons_in_strings_and_trailing_comments():
    sql = "CREATE TABLE a (x String DEFAULT 'a;b', -- a; b\n y Int8) ENGINE = MergeTree;\nSELECT 1; -- end"
    assert split_statements(sql) == [
        "CREATE TABLE a (x String DEFAULT 'a;b', \n y Int8) ENGINE = MergeTree", "SELECT 1"]


def test_a_prefix_refuses_statements_that_would_reach_the_real_tables():
    with pytest.raises(ValueError, match="prefix works only"):
        with_prefix("ALTER TABLE data_sources ADD COLUMN x Int8", "s_")
    with pytest.raises(ValueError):
        with_prefix("CREATE TABLE data_sources (x Int8) ENGINE = MergeTree", "s_")
    assert with_prefix("ALTER TABLE data_sources ADD COLUMN x Int8", "") == "ALTER TABLE data_sources ADD COLUMN x Int8"


def test_git_sha_marks_a_dirty_tree(monkeypatch):
    import subprocess

    from common import load as loader

    def fake(cmd, **kwargs):
        out = "abc123\n" if "rev-parse" in cmd else " M common/load.py\n"
        return subprocess.CompletedProcess(cmd, 0, stdout=out)

    monkeypatch.setattr(loader.subprocess, "run", fake)
    assert loader.git_sha() == "abc123-dirty"
