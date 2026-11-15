"""Build the F5 test-set audit from DS's engine_test_set rows. Pure: no I/O."""
from __future__ import annotations

from collections import Counter

from api.schemas.test_set import (
    CdlAgreementOut,
    ExpectationSummaryOut,
    ScenarioOutcomeOut,
    TestSetFieldOut,
    TestSetOut,
)

HEADLINE_SCENARIO = "every_constraint_stated"

CDL_REFERENCE = (
    "Team field-selection label (CDL crop history at selection time) compared with DS1 rules v1.0 "
    "classification of CDL 2015-2025"
)
CDL_NOTE = (
    "Agreement with another classification, not accuracy: both labels are derived from CDL, so they are not "
    "independent. With 45 fields the counts are indicative, not statistically strong."
)
# DS1's handover rows carry this scenario: an expected outcome, never an engine result.
EXPECTED_SCENARIO = "expected"

_COMMON_CAVEATS = [
    "The headline outcome is the scenario where the farmer states every constraint. Other scenarios are listed per field.",
    "A field with no expectation is not a failure: it only means nobody has written down what the evidence should support for it.",
    "Fields that abstain because they are outside the supported domain are the engine working as intended, not failures.",
    "All fields are team-drawn demonstration polygons in Story and Boone counties.",
]


# The selection notes and DS1's rules name two classes differently.
_DS1_NAME = {"corn": "continuous_corn", "pasture": "pasture_hay"}


def _cdl_agreement(per_field: dict[str, dict]) -> CdlAgreementOut:
    labelled = [f for f in per_field.values() if f["selection_label"] and f["field_class"]]
    pairs = Counter(
        (_DS1_NAME.get(f["selection_label"], f["selection_label"]), f["field_class"]) for f in labelled
    )
    agree = sum(n for (a, b), n in pairs.items() if a == b)
    return CdlAgreementOut(
        reference=CDL_REFERENCE,
        metrics={
            "fields_compared": len(labelled),
            "fields_agreeing": agree,
            "fields_disagreeing": len(labelled) - agree,
            "disagreements": [
                {"selection_label": a, "ds1_class": b, "fields": n}
                for (a, b), n in sorted(pairs.items()) if a != b
            ],
        },
        note=CDL_NOTE,
    )


def _blank(value) -> str | None:
    text = str(value or "").strip()
    return text or None


def _summary(rows: list[dict], fields: list[TestSetFieldOut]) -> ExpectationSummaryOut:
    cases = [(r, _blank(r.get("expected_outcome"))) for r in rows]
    with_expectation = [(r, e) for r, e in cases if e is not None]
    matching = sum(r["outcome"] == e for r, e in with_expectation)
    awaiting = sum(_blank(r.get("expected_review_state")) == "awaiting_review" for r, _ in with_expectation)
    if not with_expectation:
        note = (
            "No expectations have been written for this run, so there is nothing to compare the engine with. "
            "The outcomes are shown without a verdict."
        )
    else:
        note = (
            f"Only {len(with_expectation)} of {len(cases)} cases have an expectation. They were written by reading "
            "what the evidence should support, not derived from a field's crop class, which would be circular "
            "because the engine reads the same labels. The rest are blank on purpose: no expectation is better "
            "than a circular one."
        )
        note += (
            f" {awaiting} of the {len(with_expectation)} are still awaiting review, so they are not yet a benchmark."
            if awaiting
            else " All have been reviewed."
        )
    return ExpectationSummaryOut(
        cases_total=len(cases),
        cases_with_expectation=len(with_expectation),
        cases_matching=matching,
        fields_with_expectation=sum(f.expected_outcome is not None for f in fields),
        awaiting_review=awaiting,
        reviewed=len(with_expectation) - awaiting,
        note=note,
    )


def build_test_set(rows: list[dict], data_version: str) -> TestSetOut | None:
    """None when no engine run has been loaded.

    `rows` are the engine's results, one per field and scenario, each possibly carrying DS2's expected outcome and its
    review state. A row for the scenario "expected" is never an engine result. An expectation is used only where DS2
    wrote one; nothing is derived or filled in for the rest.
    """
    rows = [r for r in rows if r["scenario"] != EXPECTED_SCENARIO]
    if not rows:
        return None
    per_field: dict[str, dict] = {}
    for row in rows:
        expected = _blank(row.get("expected_outcome"))
        entry = per_field.setdefault(row["field_id"], {**row, "scenarios": []})
        entry["scenarios"].append(
            ScenarioOutcomeOut(
                scenario=row["scenario"],
                outcome=row["outcome"],
                expected_outcome=expected,
                expected_review_state=_blank(row.get("expected_review_state")) if expected else None,
                match=None if expected is None else row["outcome"] == expected,
            )
        )

    fields = []
    for entry in per_field.values():
        headline = next((s for s in entry["scenarios"] if s.scenario == HEADLINE_SCENARIO), None)
        if headline is None:
            continue
        fields.append(
            TestSetFieldOut(
                field_id=entry["field_id"], role=entry["role"], county=entry["county"],
                sequence_summary=entry["crop_history_summary"],
                expected_outcome=headline.expected_outcome,
                expected_review_state=headline.expected_review_state,
                engine_outcome=headline.outcome, match=headline.match, scenarios=entry["scenarios"],
            )
        )
    fields.sort(key=lambda f: (f.role != "primary", f.field_id))
    summary = _summary(rows, fields)
    first = rows[0]
    return TestSetOut(
        data_version=data_version, engine_version=first["rules_version"], run_id=first["run_id"],
        headline_scenario=HEADLINE_SCENARIO, fields=fields,
        outcome_counts=dict(Counter(f.engine_outcome for f in fields)),
        expectations=summary, cdl_agreement=_cdl_agreement(per_field),
        caveats=[summary.note, *_COMMON_CAVEATS],
    )
