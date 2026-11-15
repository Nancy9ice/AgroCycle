"""Build the F5 test-set audit from DS's engine_test_set rows. Pure: no I/O."""
from __future__ import annotations

from collections import Counter

from api.schemas.test_set import CdlAgreementOut, ScenarioOutcomeOut, TestSetFieldOut, TestSetOut

HEADLINE_SCENARIO = "every_constraint_stated"
WORTH_EXPLORING = "strategy_worth_exploring"
ABSTENTION = "abstention"

CDL_REFERENCE = (
    "Team field-selection label (CDL crop history at selection time) compared with DS1 rules v1.0 "
    "classification of CDL 2015-2025"
)
CDL_NOTE = (
    "Agreement with another classification, not accuracy: both labels are derived from CDL, so they are not "
    "independent. With 45 fields the counts are indicative, not statistically strong."
)
# The scenario DS1's handover rows carry: an expected outcome, not an engine result.
EXPECTED_SCENARIO = "expected"

_EXPECTED_CAVEAT = {
    "ds1_expected": (
        "The expected outcome for each field comes from DS1's handover ({basis}), not from the engine, so the "
        "comparison is between two separate judgements. It is DS1's expectation, not ground truth."
    ),
    "selection_label": (
        "No expected outcomes were loaded, so the expectation is derived from the team's field-selection label: "
        "rotation fields should reach a strategy comparison, every other class should abstain. It is not an "
        "independent ground truth."
    ),
    "mixed": (
        "Expected outcomes came from DS1's handover ({basis}) for most fields; the rest are derived from the "
        "team's field-selection label. Neither is ground truth."
    ),
}

_COMMON_CAVEATS = [
    "The headline outcome is the scenario where the farmer states every constraint. Other scenarios are listed per field.",
    "Fields that abstain because they are outside the supported domain are the engine working as intended, not failures.",
    "All fields are team-drawn demonstration polygons in Story and Boone counties.",
]


# The selection notes and DS1's rules name two classes differently.
_DS1_NAME = {"corn": "continuous_corn", "pasture": "pasture_hay"}


def expected_outcome(selection_label: str | None) -> str:
    return WORTH_EXPLORING if selection_label == "rotation" else ABSTENTION


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


def build_test_set(rows: list[dict], data_version: str, expected: dict | None = None) -> TestSetOut | None:
    """None when no engine run has been loaded.

    `rows` are the engine's results, one per field and scenario. `expected` is DS1's expected outcome per field
    (`{"run_id", "rules_version", "by_field"}`) or None. A row for the scenario "expected" is never an engine result.
    """
    rows = [r for r in rows if r["scenario"] != EXPECTED_SCENARIO]
    if not rows:
        return None
    given = (expected or {}).get("by_field", {})
    per_field: dict[str, dict] = {}
    for row in rows:
        entry = per_field.setdefault(row["field_id"], {**row, "scenarios": []})
        entry["scenarios"].append(ScenarioOutcomeOut(scenario=row["scenario"], outcome=row["outcome"]))

    fields = []
    used_ds1: list[bool] = []
    for entry in per_field.values():
        by_scenario = {s.scenario: s.outcome for s in entry["scenarios"]}
        engine = by_scenario.get(HEADLINE_SCENARIO)
        if engine is None:
            continue
        from_ds1 = entry["field_id"] in given
        expected_for_field = given[entry["field_id"]] if from_ds1 else expected_outcome(entry["selection_label"])
        used_ds1.append(from_ds1)
        fields.append(TestSetFieldOut(
            field_id=entry["field_id"], role=entry["role"], county=entry["county"],
            sequence_summary=entry["crop_history_summary"],
            expected_outcome=expected_for_field, engine_outcome=engine, match=engine == expected_for_field,
            scenarios=entry["scenarios"],
        ))
    fields.sort(key=lambda f: (f.role != "primary", f.field_id))
    source = "ds1_expected" if used_ds1 and all(used_ds1) else "mixed" if any(used_ds1) else "selection_label"
    basis = (
        f"run {expected['run_id']}, rules {expected['rules_version']}" if expected and source != "selection_label" else ""
    )
    first = rows[0]
    return TestSetOut(
        data_version=data_version, engine_version=first["rules_version"], run_id=first["run_id"],
        headline_scenario=HEADLINE_SCENARIO, fields=fields,
        outcome_counts=dict(Counter(f.engine_outcome for f in fields)),
        match_count=sum(f.match for f in fields),
        cdl_agreement=_cdl_agreement(per_field),
        expected_source=source, expected_basis=basis,
        caveats=[_EXPECTED_CAVEAT[source].format(basis=basis), *_COMMON_CAVEATS],
    )
