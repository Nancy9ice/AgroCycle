"""Expected outcomes for the test-set audit (AgroCycle, DS2; BE's F5 follow-up).

BE asked for an `expected_outcome` per field so the endpoint can show engine against expectation. He also
spotted the trap himself: deriving it from the team's field-selection labels is circular, because the engine
reads those same labels. An expectation that comes from the thing being tested measures nothing.

So the expectations here come from the validation matrix, where each case was written by reading what the
evidence should support, and they are published with their review state attached. Until DS1 and BE have
signed the matrix off, every row says `awaiting_review`, and the endpoint should say so rather than present
an unreviewed expectation as a benchmark.

Only (field, scenario) pairs a matrix case genuinely describes get an expectation. Everything else is left
null on purpose: no expectation is better than a circular one.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:  # the matrix lives beside the tests, not in an installed package
    sys.path.insert(0, str(REPO_ROOT))

from engine.tests.test_validation_matrix import MATRIX, REVIEWED_BY

# A matrix case only maps onto a real row where it genuinely describes that field in that scenario.
# `1-complete-evidence` and `5-no-manure` describe the primary field; `3-partial-soil` is test-022, whose
# organic matter covers 96.72 % of it; `8-out-of-domain-history` is test-027, a continuous-corn field.
CASE_TO_ROW: dict[str, tuple[str, str]] = {
    "1-complete-evidence": ("primary-001", "every_constraint_stated"),
    "5-no-manure": ("primary-001", "no_manure"),
    "3-partial-soil": ("test-022", "every_constraint_stated"),
    "8-out-of-domain-history": ("test-027", "every_constraint_stated"),
}

AWAITING = "awaiting_review"
REVIEWED = "reviewed"


def review_state() -> str:
    return REVIEWED if REVIEWED_BY else AWAITING


def expected_rows() -> list[dict]:
    """One row per matrix case: the expectation, why, and whether anyone has checked it."""
    state = review_state()
    reviewers = ", ".join(REVIEWED_BY)
    rows = []
    for case_id, _, _, expected, why in MATRIX:
        field_id, scenario = CASE_TO_ROW.get(case_id, ("", ""))
        rows.append(
            {
                "case_id": case_id,
                "field_id": field_id,
                "scenario": scenario,
                "expected_outcome": expected,
                "expected_reason": why,
                "review_state": state,
                "reviewed_by": reviewers,
                "source": (
                    "engine/tests/test_validation_matrix.py, written by reading what the evidence should "
                    "support rather than from the labels the engine reads"
                ),
            }
        )
    return rows


def expectation_for(field_id: str, scenario: str) -> dict | None:
    """The expectation for one audit row, or None where nobody has stated one."""
    for row in expected_rows():
        if row["field_id"] == field_id and row["scenario"] == scenario:
            return row
    return None
