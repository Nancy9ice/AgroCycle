
from api.facts import IndicatorFacts
from api.repository import ClickHouseRepository, FileRepository


def test_file_repository_lists_all_45_demo_fields_primary_first(repository):
    fields = repository.list_fields()
    assert len(fields) == 45
    assert fields[0].field_id == "primary-001"
    assert sum(1 for f in fields if f.field_class == "rotation") == 27
    assert all(f.boundary_source == "demo" for f in fields)


def test_unknown_field_is_none(repository):
    assert repository.get_field("nope") is None


def test_no_indicator_outputs_means_nothing_known(repository):
    assert repository.get_indicators("primary-001") == IndicatorFacts()


def test_indicator_outputs_are_reduced_to_what_the_engine_reads(indicator_dir):
    repo = FileRepository(indicators_dir=indicator_dir)
    facts = repo.get_indicators("primary-001")
    assert facts.statuses == {
        "gdd": "ok",
        "precipitation_total": "ok",
        "frost_window": "ok",
        "om_r_0_30cm": "ok",
    }
    assert facts.gdd_season_difference_vs_marsden == 80.0
    assert facts.frost_free_days == 155  # mean of 150 and 160
    assert facts.dominant_drainage_class == "Poorly drained"  # the larger share


def test_a_field_missing_from_the_outputs_is_unknown(indicator_dir):
    repo = FileRepository(indicators_dir=indicator_dir)
    assert repo.get_indicators("test-001") == IndicatorFacts()


class FakeResult:
    def __init__(self, rows):
        self.result_rows = rows


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.queries: list[tuple[str, dict | None]] = []

    def query(self, sql, parameters=None):
        self.queries.append((sql, parameters))
        return FakeResult(self.rows)


ROW = ("primary-001", "primary", "demo", "Story", "rotation", "SCSCSCSCSCS")


def test_clickhouse_repository_maps_rows_without_the_live_database():
    client = FakeClient([("test-001", "test", "demo", "Story", None, None), ROW])
    fields = ClickHouseRepository(client).list_fields()
    assert [f.field_id for f in fields] == ["primary-001", "test-001"]
    assert fields[1].field_class is None and fields[1].crop_sequence is None


def test_clickhouse_lookup_is_parameterised_never_string_built():
    client = FakeClient([ROW])
    ClickHouseRepository(client).get_field("primary-001'; DROP TABLE fields; --")
    sql, parameters = client.queries[0]
    assert "DROP" not in sql
    assert parameters == {"field_id": "primary-001'; DROP TABLE fields; --"}


def test_clickhouse_reports_no_indicators_until_the_table_exists():
    assert ClickHouseRepository(FakeClient([])).get_indicators("x") == IndicatorFacts()
