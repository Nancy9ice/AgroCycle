import pytest

from api.core.crop_summary import describe_sequence
from api.core.drawn_field import SEASONS, CropHistoryError, classify_crops


def test_alternating_corn_and_soy_is_a_rotation_by_ds1s_rules():
    crops = ["corn", "soybeans"] * 5 + ["corn"]
    sequence, field_class = classify_crops(crops)
    assert sequence == "CSCSCSCSCSC" and field_class == "rotation"


def test_the_same_rules_classify_the_other_classes():
    assert classify_crops(["corn"] * SEASONS) == ("C" * SEASONS, "continuous_corn")
    assert classify_crops(["pasture_hay"] * SEASONS)[1] == "pasture_hay"
    assert classify_crops(["oats", "alfalfa"] * 5 + ["oats"])[1] == "other"


def test_a_history_with_a_few_repeats_is_not_a_rotation():
    # 7 alternations are needed; this has only 5 of 10 transitions between corn and soybeans.
    crops = ["corn", "soybeans", "corn", "soybeans", "corn", "soybeans", "soybeans", "soybeans", "corn", "corn", "corn"]
    assert classify_crops(crops)[1] != "rotation"


def test_the_sequence_uses_codes_the_profile_can_describe():
    sequence, _ = classify_crops(["corn", "soybeans"] * 5 + ["corn"])
    assert "alternate" in describe_sequence(sequence, 2015)  # the web and API sentence builder accepts it


@pytest.mark.parametrize("crops", [[], ["corn"] * 10, ["corn"] * 12])
def test_all_eleven_seasons_are_required(crops):
    with pytest.raises(CropHistoryError, match="all 11 seasons"):
        classify_crops(crops)


def test_an_unknown_crop_is_refused_not_guessed():
    with pytest.raises(CropHistoryError, match="Unknown crop: wheat"):
        classify_crops(["wheat"] + ["corn"] * 10)
