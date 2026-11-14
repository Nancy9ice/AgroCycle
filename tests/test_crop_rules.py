"""DS1's rules v1.0, tested at their boundaries."""

import pytest

from transform.crop_history import rules

CODE = {"C": 1, "S": 5, "O": 28, "A": 36, "P": 176, "N": 121, "X": 27}


def year(token: str) -> rules.YearLabel:
    """A synthetic year: 100 pixels, all one class, or the mixed / low-confidence patterns."""
    if token == "M":  # no group reaches 60 %
        return rules.label_year({1: 50, 5: 50})
    if token == "L":  # 30 % no-data
        return rules.label_year({1: 70, 0: 30})
    return rules.label_year({CODE[token]: 100})


def field(sequence: str, first_year: int = 2015) -> rules.FieldClass:
    labels = {first_year + i: year(t) for i, t in enumerate(sequence.split())}
    return rules.classify_field(labels)


def test_no_code_belongs_to_two_groups():
    groups = list(rules.GROUPS.values())
    for i, a in enumerate(groups):
        for b in groups[i + 1:]:
            assert not a & b


@pytest.mark.parametrize("code, group", [
    (1, "corn"), (225, "corn"), (5, "soybeans"), (26, "soybeans"), (28, "oats"), (36, "alfalfa"),
    (176, "pasture_hay"), (37, "pasture_hay"), (121, "non_crop"), (0, "non_crop"),
])
def test_class_groups(code, group):
    assert rules.class_group(code) == group and rules.is_listed(code)


def test_a_code_the_rules_do_not_mention_is_other_crop_and_flagged_not_an_error():
    assert rules.class_group(27) == "other_crop" and not rules.is_listed(27)
    label = rules.label_year({27: 100})
    assert label.group == "other_crop" and label.status == "ok"


def test_the_dominant_threshold_is_60_percent_inclusive():
    assert rules.label_year({1: 60, 5: 40}).status == "ok"
    exactly = rules.label_year({1: 60, 5: 40})
    assert exactly.group == "corn" and exactly.dominant_share_pct == 60
    just_under = rules.label_year({1: 59, 5: 41})
    assert just_under.status == "mixed_uncertain" and just_under.group == "mixed"


def test_groups_not_codes_are_compared_so_double_crops_add_to_their_group():
    assert rules.label_year({1: 30, 225: 30, 5: 40}).group == "corn"  # 60 % corn group
    assert rules.label_year({5: 35, 26: 30, 1: 35}).group == "soybeans"  # 65 % soybean group


def test_no_data_above_20_percent_is_low_confidence_and_exactly_20_is_not():
    assert rules.label_year({1: 80, 0: 20}).status == "ok"
    low = rules.label_year({1: 79, 0: 21})
    assert low.status == "low_confidence" and low.nodata_share_pct == 21


def test_a_field_year_without_pixels_cannot_be_labelled():
    with pytest.raises(ValueError):
        rules.label_year({})


def test_ds1_example_primary_field_is_a_rotation_with_ten_alternations():
    result = field("S C S C S C S C S C S")
    assert result.field_class == "rotation"
    assert result.sequence == "S C S C S C S C S C S"
    assert (result.alternations, result.transitions_counted) == (10, 10)


def test_rotation_needs_7_alternations_and_6_do_not_make_one():
    seven = field("C S C S C S C S S S S")
    assert seven.alternations == 7 and seven.field_class == "rotation"
    six = field("C S C S C S C C C C C")
    assert six.alternations == 6 and six.field_class == "continuous_corn"  # 8 corn years, not 7 of 10


def test_continuous_corn_needs_8_corn_years_and_7_fall_through_to_mixed():
    assert field("C C C C C C C C S S S").field_class == "continuous_corn"
    seven = field("C C C C C C C S S S S")
    assert seven.corn_years == 7 and seven.field_class == "mixed"


def test_pasture_hay_needs_8_years_and_the_dominant_group_must_be_pasture_not_alfalfa():
    assert field("P P P P P P P P N N N").field_class == "pasture_hay"
    assert field("P P P P P P P N N N N").field_class == "other"  # 7 pasture years, under 5 corn/soy years
    alfalfa = field("A A A A A A A A A A A")
    assert alfalfa.field_class == "other"  # alfalfa is in no pasture/hay rule: the gap DS1 must settle


def test_mixed_needs_5_corn_or_soy_years_otherwise_other():
    assert field("C S S N N N N N N N N").field_class == "other"
    assert field("C C C S S N N N N N N").field_class == "mixed"


def test_rotation_is_checked_first_even_when_mixed_also_fits():
    result = field("S C S C S C S C S C S")
    assert result.corn_years + result.soybean_years >= rules.MIXED_MIN_CORN_SOY_YEARS
    assert result.field_class == "rotation"


def test_mixed_and_low_confidence_years_leave_their_transitions_out_of_the_count():
    result = field("S C S M S C S C S C S")
    assert result.transitions_counted == 8  # the two transitions touching the mixed year are skipped
    assert result.alternations == 8 and result.field_class == "rotation"
    low = field("S C S L S C S C S C S")
    assert low.sequence.split()[3] == "L" and low.transitions_counted == 8


def test_a_year_of_another_crop_counts_against_the_rotation():
    result = field("S C S C S C S C O O O")
    assert result.transitions_counted == 10 and result.alternations == 7


def test_only_the_last_11_years_are_used():
    labels = {y: year("C") for y in range(2008, 2015)}
    labels.update({2015 + i: year(t) for i, t in enumerate(["S", "C", "S", "C", "S", "C", "S", "C", "S", "C", "S"])})
    result = rules.classify_field(labels)
    assert result.years == tuple(range(2015, 2026)) and result.field_class == "rotation"
