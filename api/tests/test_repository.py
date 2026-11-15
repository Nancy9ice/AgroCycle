from datetime import date

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
    """Answers each table's query from its own list of rows, and records every query it was sent."""

    def __init__(self, fields=(), indicators=(), soil=(), fail=False):
        self.fields, self.indicators, self.soil, self.fail = fields, indicators, soil, fail
        self.queries: list[tuple[str, dict | None]] = []

    def query(self, sql, parameters=None):
        self.queries.append((sql, parameters))
        if self.fail:
            raise ConnectionError("clickhouse is down")
        if "FROM field_indicators" in sql:
            return FakeResult(self.indicators)
        if "FROM soil_properties" in sql:
            return FakeResult(self.soil)
        return FakeResult(self.fields)


ROW = ("primary-001", "primary", "demo", "Story", "rotation")


def indicator_tuple(indicator_id, value, status="available", unit="mm", year=2015, reason=None):
    return (
        "primary-001",
        indicator_id,
        value,
        unit,
        status,
        date(year, 4, 1),
        date(year, 11, 30),
        reason,
    )


# The same logical rows, once as ClickHouse tuples and once as the CSV the runner writes.
SEASONS = [
    indicator_tuple("precipitation_total", 600.0, year=2015),
    indicator_tuple("precipitation_total", 700.0, year=2016),
    indicator_tuple("precipitation_total", 100.0, status="partial", year=2017),
    indicator_tuple("gdd", 1500.0, unit="degree-days C", year=2015),
    indicator_tuple("heat_days", None, status="unknown", unit="days", year=2015),
    indicator_tuple("frost_free_days", 150.0, unit="days"),
    indicator_tuple("frost_free_days", 160.0, unit="days", year=2016),
    indicator_tuple("om_r_0_30cm", 3.1, unit="% by weight"),
    indicator_tuple("claytotal_r_0_30cm", 27.0, unit="% by weight"),
    indicator_tuple(
        "sandtotal_r_0_30cm",
        31.7,
        status="partial",
        unit="% by weight",
        reason="computed over 100.00% of the field's mapped area, depth 99.28%",
    ),
    indicator_tuple("silttotal_r_0_30cm", None, status="unknown", unit="% by weight"),
    indicator_tuple("gdd_season_difference_vs_marsden", 80.0, unit="degree-days C"),
]
SOIL = [
    ("primary-001", "drainagecl", "Somewhat poorly drained", 30.0),
    ("primary-001", "drainagecl", "Poorly drained", 70.0),
]


def as_csv_rows(tuples):
    return [
        {
            "field_id": f,
            "indicator_id": i,
            "category": "x",
            "value": "" if v is None else str(v),
            "unit": u,
            "status": st,
            "window_start": ws.isoformat(),
            "window_end": we.isoformat(),
            "valid_obs": "1",
            "unknown_reason": reason or "",
            "run_id": "t",
        }
        for f, i, v, u, st, ws, we, reason in tuples
    ]


def test_clickhouse_and_files_give_identical_facts_from_identical_rows(tmp_path):
    from .conftest import soil_row, write_csv

    write_csv(tmp_path / "field_indicators.csv", as_csv_rows(SEASONS))
    write_csv(
        tmp_path / "soil_properties.csv",
        [soil_row("primary-001", "drainagecl", label, str(share)) for _, _, label, share in SOIL],
    )
    from_files = FileRepository(indicators_dir=tmp_path).get_indicators("primary-001")
    from_clickhouse = ClickHouseRepository(FakeClient(indicators=SEASONS, soil=SOIL)).get_indicators(
        "primary-001"
    )
    assert from_clickhouse == from_files
    assert from_clickhouse.statuses["frost_window"] == "ok"
    assert from_clickhouse.dominant_drainage_class == "Poorly drained"


def test_partial_and_unknown_seasons_never_count_in_clickhouse_either():
    facts = ClickHouseRepository(FakeClient(indicators=SEASONS)).get_indicators("primary-001")
    rain = facts.seasonal["precipitation_total"]
    assert (rain.mean, rain.seasons_used, rain.seasons_total) == (650.0, 2, 3)
    assert "heat_days" not in facts.seasonal
    assert facts.statuses["precipitation_total"] == "unknown"  # one partial season


def test_a_field_with_no_rows_is_unknown_not_an_error():
    assert ClickHouseRepository(FakeClient()).get_indicators("primary-001") == IndicatorFacts()


def test_indicator_and_soil_queries_are_parameterised_never_string_built():
    client = FakeClient()
    hostile = "primary-001'; DROP TABLE field_indicators; --"
    repo = ClickHouseRepository(client)
    repo.get_indicators(hostile)
    repo.get_field(hostile)
    assert len(client.queries) == 3
    for sql, parameters in client.queries:
        assert "DROP" not in sql
        assert parameters == {"field_id": hostile}


def test_a_database_failure_raises_instead_of_looking_like_missing_data():
    repo = ClickHouseRepository(FakeClient(fail=True))
    import pytest

    with pytest.raises(ConnectionError):
        repo.get_indicators("primary-001")
    with pytest.raises(ConnectionError):
        repo.get_field("primary-001")


def test_clickhouse_supplies_the_class_and_the_committed_notes_supply_sequence_and_soil(repository):
    repo = ClickHouseRepository(FakeClient(fields=[ROW]), notes=repository)
    record = repo.get_field("primary-001")
    assert record.field_class == "rotation"  # from ClickHouse
    assert record.crop_sequence == "SCSCSCSCSCS"  # from the notes, not crop_rotation.sequence
    assert record.soil_series == "Nicollet"


def test_a_field_in_clickhouse_but_not_in_the_notes_still_loads_without_crop_history(repository):
    row = ("test-999", "test", "demo", "Boone", "rotation")
    record = ClickHouseRepository(FakeClient(fields=[row]), notes=repository).get_field("test-999")
    assert record.crop_sequence is None and record.soil_series is None


def test_the_query_never_asks_for_the_incompatible_sequence_column():
    client = FakeClient(fields=[ROW])
    ClickHouseRepository(client).list_fields()
    assert "sequence" not in client.queries[0][0]


def test_the_check_command_describes_what_the_api_would_read(repository):
    from api.check_clickhouse import describe

    repo = ClickHouseRepository(FakeClient(fields=[ROW], indicators=SEASONS, soil=SOIL), notes=repository)
    text = "\n".join(describe(repo, "primary-001"))
    assert "Poorly drained" in text
    assert "precipitation_total: mean 650.0 mm over 2 of 3 seasons" in text
    assert describe(ClickHouseRepository(FakeClient()), "nope") == [
        "no field 'nope' in ClickHouse `fields`"
    ]


def test_a_season_that_does_not_state_its_dates_is_left_out_of_the_average():
    from api.repository import seasonal_means

    def row(value, start, end):
        return {
            "indicator_id": "gdd",
            "status": "available",
            "value": value,
            "unit": "degree-days C",
            "window_start": start,
            "window_end": end,
        }

    result = seasonal_means([row("1500", "2015-04-01", "2015-11-30"), row("9999", "", "")])
    assert result["gdd"].mean == 1500.0
    assert (result["gdd"].seasons_used, result["gdd"].seasons_total) == (1, 2)


def test_soil_measures_keep_a_partial_value_with_its_coverage_note_and_drop_an_unknown_one():
    facts = ClickHouseRepository(FakeClient(indicators=SEASONS)).get_indicators("primary-001")
    assert facts.soil["om_r_0_30cm"].value == 3.1 and facts.soil["om_r_0_30cm"].coverage_note == ""
    sand = facts.soil["sandtotal_r_0_30cm"]
    assert sand.value == 31.7 and "99.28%" in sand.coverage_note
    assert "silttotal_r_0_30cm" not in facts.soil  # unknown: omitted, not zero


def test_drainage_keeps_the_whole_mix_largest_first():
    facts = ClickHouseRepository(FakeClient(soil=SOIL)).get_indicators("primary-001")
    assert facts.drainage_shares == (("Poorly drained", 70.0), ("Somewhat poorly drained", 30.0))
