"""The same cases as web/src/features/profile/build-crop-history.test.ts."""
import pytest

from api.core.crop_summary import describe_sequence


def test_clean_alternation():
    assert describe_sequence("SCSCSCSCSCS", 2015) == (
        "Corn and soybeans alternate every year, 2015 to 2025: the pattern AgroCycle is built for."
    )


def test_names_the_year_a_crop_repeats():
    text = describe_sequence("SCCSCSCSCSC", 2015)
    assert "mostly alternating" in text
    assert "one year: corn in 2017" in text


def test_names_several_repeated_years():
    assert "2 years: soybean in 2019 and corn in 2023" in describe_sequence("CSCSSCSCCSC", 2015)


def test_corn_heavy_history_is_not_called_alternating():
    assert "alternat" not in describe_sequence("CCCSCCSCCSC", 2015)


def test_single_crop():
    assert describe_sequence("GGGGGGGGGGG", 2015) == "Grass or pasture in every year, 2015 to 2025."


def test_a_mix_lists_the_most_frequent_crop_first():
    assert describe_sequence("CCCSCCSCCSC", 2015) == (
        "A mix of crops, 2015 to 2025: corn 8 years, soybean 3 years."
    )


@pytest.mark.parametrize("sequence", ["", "CZ"])
def test_unusable_sequences_raise_instead_of_guessing(sequence):
    with pytest.raises(ValueError):
        describe_sequence(sequence, 2015)
