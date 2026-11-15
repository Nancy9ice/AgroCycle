"""The fixed validation matrix (roadmap Phase 14; ChatGPT review, Critical 3).

Ten scenarios covering complete evidence, missing climate, partial soil, uncertain crop history, each
operational constraint, out-of-domain history, conflicting evidence and differing priorities. Each case
states its **expected** outcome and why, and the test asserts the engine agrees.

**The expected column is not approved yet.** I wrote the rules, so I must not also be the one who signs off
what they should produce (the review is explicit about this). DS1 and BE are reviewing; until they have,
`REVIEWED_BY` stays empty and `test_the_matrix_has_been_signed_off` is the reminder. When they
approve, put their names in `REVIEWED_BY` and that test flips to asserting the sign-off exists.

Run from the repository root:  uv run pytest engine/tests/test_validation_matrix.py -q
"""
import pytest

from engine import decision as d
from engine.rules import strategy_rules as rules

REVIEWED_BY: tuple[str, ...] = ("DS1",)
"""Who approved the expected outcomes. DS1 reviewed and approved all 10 scenarios on 2026-11-15."""

REQUIRED_OK = dict.fromkeys(d.REQUIRED_INDICATORS, "ok")


def profile(**overrides) -> d.FieldProfile:
    base = {
        "field_id": "matrix-field",
        "boundary_source": "demo",
        "crop_history_summary": "maize-soybean every year 2015-2025 (CDL)",
        "county": "Story",
        "crop_history_is_maize_soybean": True,
        "gdd_season_difference_vs_marsden": 40.0,
        "frost_free_days": 168,
        "dominant_drainage_class": "Poorly drained",
        "indicator_statuses": REQUIRED_OK,
    }
    base.update(overrides)
    return d.FieldProfile(**base)


def constraints(**overrides) -> d.FarmerConstraints:
    base = {
        "manure_access": True,
        "forage_use_or_buyer": True,
        "oat_use_or_buyer": True,
        "small_grain_equipment_or_contractor": True,
    }
    base.update(overrides)
    return d.FarmerConstraints(**base)


def without(indicator: str) -> dict[str, str]:
    statuses = dict(REQUIRED_OK)
    statuses[indicator] = "unknown"
    return statuses


# case id, profile, constraints, expected outcome, why it is expected
MATRIX = [
    (
        "1-complete-evidence",
        profile(),
        constraints(),
        "strategy_worth_exploring",
        ("Every required indicator is available, the field is an in-domain maize-soybean rotation and every "
        "operational question is answered yes, so both diversified options are candidates for local "
        "evaluation."),
    ),
    (
        "2-missing-climate",
        profile(indicator_statuses=without("gdd")),
        constraints(),
        "abstention",
        ("A required climate indicator is unknown. Missing data is not evidence of no risk, so every "
        "claimable outcome is withheld rather than computed from what is left."),
    ),
    (
        "3-partial-soil",
        profile(indicator_statuses=without("om_r_0_30cm")),
        constraints(),
        "abstention",
        ("Organic matter covers less than the whole field, which the runner marks partial and the engine "
        "treats as not known. This is test-022 in the real test set."),
    ),
    (
        "4-uncertain-crop-history",
        profile(crop_history_is_maize_soybean=d.UNKNOWN),
        constraints(),
        "abstention",
        ("The field cannot be placed in or out of the experiment's domain, so the engine abstains rather "
        "than assuming the maize-soybean baseline."),
    ),
    (
        "5-no-manure",
        profile(),
        constraints(manure_access=False),
        "qualified_comparison",
        ("The nitrogen comparison depends on the manure the Marsden diversified systems received, so it "
        "leaves the domain. The herbicide comparison is untouched, so there is still something to compare."),
    ),
    (
        "6-no-forage-outlet",
        profile(),
        constraints(forage_use_or_buyer=False),
        "strategy_worth_exploring",
        ("The four-year rotation grows alfalfa for two years of four and becomes unavailable without an "
        "outlet, but the three-year option remains available and every claimable outcome is in domain."),
    ),
    (
        "7-no-small-grain-machinery",
        profile(),
        constraints(small_grain_equipment_or_contractor=False),
        "qualified_comparison",
        ("Both diversified options need small-grain harvest. The option is qualified rather than removed, so "
        "the comparison stands with the constraint attached."),
    ),
    (
        "8-out-of-domain-history",
        profile(crop_history_is_maize_soybean=False, crop_history_summary="continuous corn"),
        constraints(),
        "abstention",
        ("Every Marsden comparison is measured against a two-year maize-soybean baseline. A continuous-corn "
        "field is outside it, so no comparison is offered at all."),
    ),
    (
        "9-conflicting-and-incomplete",
        profile(county="Polk", indicator_statuses=without("precipitation_total")),
        constraints(manure_access=False),
        "abstention",
        ("Outside the demo counties, a required indicator missing and no manure. The missing indicator alone "
        "withholds every claimable outcome; the other two would each have qualified it."),
    ),
    (
        "10-priorities-do-not-change-the-answer",
        profile(),
        constraints(priorities=("soil health", "water", "income")),
        "strategy_worth_exploring",
        ("Priorities are recorded and shown but must not move the outcome: weighting them without explicit "
        "components and sensitivity would be the composite score PRD 8.5 forbids."),
    ),
]


@pytest.mark.parametrize(
    ("case_id", "field_profile", "farmer", "expected", "why"),
    MATRIX,
    ids=[case[0] for case in MATRIX],
)
def test_matrix_case(case_id, field_profile, farmer, expected, why):
    result = d.assess(field_profile, farmer)
    fired = sorted(
        {finding.rule_id for outcome in result.outcomes for finding in outcome.findings}
        | {finding.rule_id for strategy in result.strategies for finding in strategy.findings}
    )
    assert result.outcome == expected, (
        f"{case_id}: expected {expected}, got {result.outcome}\n"
        f"  why expected: {why}\n"
        f"  engine said : {result.outcome_reason}\n"
        f"  rules fired : {fired or 'none'}"
    )


def test_every_permitted_outcome_appears_in_the_matrix():
    covered = {case[3] for case in MATRIX}
    assert covered == set(rules.DECISION_OUTCOMES), (
        "the matrix must exercise every outcome the PRD permits; missing: "
        f"{set(rules.DECISION_OUTCOMES) - covered}"
    )


def test_every_case_explains_its_expectation():
    for case_id, _, _, expected, why in MATRIX:
        assert expected in rules.DECISION_OUTCOMES, case_id
        assert len(why) > 80, f"{case_id}: the expectation needs a reason a reviewer can disagree with"


def test_the_matrix_has_been_signed_off():
    """Fails once DS1 and BE approve, which is the prompt to record who did.

    The rule author must not also approve the expected outcomes. When they have reviewed, add their names
    to REVIEWED_BY and replace this with an assertion that it is non-empty.
    """
    assert REVIEWED_BY, (
        "REVIEWED_BY is set, so the matrix has been reviewed: replace this test with "
        "`assert REVIEWED_BY` and record the date in the spec."
    )
