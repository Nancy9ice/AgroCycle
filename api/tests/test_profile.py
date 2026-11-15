from api.facts import FieldRecord, IndicatorFacts
from api.profile import build_profile, crop_history_summary, indicator_statuses
from engine import decision as engine

from .conftest import indicator_row

ROTATION = FieldRecord("f1", "Story", "demo", "primary", "rotation", "SCSCSCSCSCS")


def test_frost_free_days_is_mapped_to_the_engines_frost_window():
    statuses = indicator_statuses([indicator_row("f1", "frost_free_days", "150")])
    assert statuses == {"frost_window": "ok"}


def test_an_indicator_is_ok_only_if_every_season_is_available():
    rows = [
        indicator_row("f1", "gdd", "1", "available"),
        indicator_row("f1", "gdd", "1", "partial"),
        indicator_row("f1", "precipitation_total", "1", "available"),
        indicator_row("f1", "precipitation_total", "1", "unknown"),
    ]
    assert indicator_statuses(rows) == {"gdd": "unknown", "precipitation_total": "unknown"}


def test_unrelated_indicators_are_ignored():
    assert indicator_statuses([indicator_row("f1", "heat_days", "3")]) == {}


def test_a_missing_class_is_unknown_not_out_of_domain():
    profile = build_profile(FieldRecord("f1", "Story", "demo", "test", None, None), IndicatorFacts())
    assert profile.crop_history_is_maize_soybean is engine.UNKNOWN
    assert "not loaded" in profile.crop_history_summary


def test_only_the_rotation_class_is_in_domain():
    for field_class, expected in [("rotation", True), ("continuous_corn", False), ("pasture_hay", False)]:
        record = FieldRecord("f1", "Story", "demo", "test", field_class, "CCCCCCCCCCC")
        assert build_profile(record, IndicatorFacts()).crop_history_is_maize_soybean is expected


def test_nothing_known_stays_unknown():
    profile = build_profile(ROTATION, IndicatorFacts())
    assert profile.gdd_season_difference_vs_marsden is engine.UNKNOWN
    assert profile.frost_free_days is engine.UNKNOWN
    assert profile.dominant_drainage_class is engine.UNKNOWN
    assert profile.unknown_required_indicators() == engine.REQUIRED_INDICATORS


def test_sample_indicators_make_the_required_set_known():
    profile = build_profile(ROTATION, IndicatorFacts(), sample_indicators=True)
    assert profile.unknown_required_indicators() == ()
    assert profile.gdd_season_difference_vs_marsden == 120.0


def test_summary_matches_the_web_wording():
    assert "alternate every year" in crop_history_summary(ROTATION)
