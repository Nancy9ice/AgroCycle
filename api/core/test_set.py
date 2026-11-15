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
CAVEATS = [
    (
        "Expected outcome comes from the team's field-selection label: rotation fields should reach a strategy "
        "comparison, every other class should abstain. It is not an independent ground truth."
    ),
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


def build_test_set(rows: list[dict], data_version: str) -> TestSetOut | None:
    """None when no audit has been loaded."""
    if not rows:
        return None
    per_field: dict[str, dict] = {}
    for row in rows:
        entry = per_field.setdefault(row["field_id"], {**row, "scenarios": []})
        entry["scenarios"].append(ScenarioOutcomeOut(scenario=row["scenario"], outcome=row["outcome"]))

    fields = []
    for entry in per_field.values():
        by_scenario = {s.scenario: s.outcome for s in entry["scenarios"]}
        engine = by_scenario.get(HEADLINE_SCENARIO)
        if engine is None:
            continue
        expected = expected_outcome(entry["selection_label"])
        fields.append(TestSetFieldOut(
            field_id=entry["field_id"], role=entry["role"], county=entry["county"],
            sequence_summary=entry["crop_history_summary"],
            expected_outcome=expected, engine_outcome=engine, match=engine == expected,
            scenarios=entry["scenarios"],
        ))
    fields.sort(key=lambda f: (f.role != "primary", f.field_id))
    first = rows[0]
    return TestSetOut(
        data_version=data_version, engine_version=first["rules_version"], run_id=first["run_id"],
        headline_scenario=HEADLINE_SCENARIO, fields=fields,
        outcome_counts=dict(Counter(f.engine_outcome for f in fields)),
        match_count=sum(f.match for f in fields),
        cdl_agreement=_cdl_agreement(per_field), caveats=CAVEATS,
    )
