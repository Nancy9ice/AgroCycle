"""Run the decision engine over every field and report the spread (AgroCycle, DS2, roadmap Phase 14).

Reads the indicator tables the Phase 4 runner wrote and the field file, builds a profile per field, and
assesses each under three constraint scenarios. Reports which outcomes occur, which rules fire and which
never fire — a rule that never fires on the whole test set is either a guardrail for input we do not have, or
a rule whose threshold is wrong.

Usage from the repository root:

    uv run python -m engine.sweep
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from collections import Counter
from pathlib import Path

import pandas as pd

from engine.decision import UNKNOWN, FarmerConstraints, FieldProfile, assess
from engine.rules import strategy_rules as rules

REPO_ROOT = Path(__file__).resolve().parents[1]
INDICATORS_PATH = REPO_ROOT / "data" / "out" / "indicators" / "field_indicators.csv"
FIELDS_PATH = REPO_ROOT / "data" / "fields" / "fields.geojson"
IN_DOMAIN_NOTE = "in-domain: maize-soybean rotation"
DEFAULT_OUT = REPO_ROOT / "data" / "out" / "validation"
DOMINANT_PREFIX = "dominant class: "

SCENARIOS = {
    "every constraint stated": FarmerConstraints(True, True, True, True),
    "no manure": FarmerConstraints(False, True, True, True),
    "nothing stated": FarmerConstraints(),
}


def _latest(indicators: pd.DataFrame) -> pd.DataFrame:
    return indicators.sort_values("window_end").groupby(["field_id", "indicator_id"]).last()


def _value(latest: pd.DataFrame, field_id: str, indicator_id: str):
    try:
        row = latest.loc[(field_id, indicator_id)]
    except KeyError:
        return UNKNOWN
    return UNKNOWN if pd.isna(row["value"]) else row["value"]


def _dominant_class(latest: pd.DataFrame, field_id: str, indicator_id: str):
    try:
        reason = latest.loc[(field_id, indicator_id)]["unknown_reason"]
    except KeyError:
        return UNKNOWN
    if isinstance(reason, str) and reason.startswith(DOMINANT_PREFIX):
        return reason.removeprefix(DOMINANT_PREFIX)
    return UNKNOWN


def _indicator_statuses(indicators: pd.DataFrame, field_id: str) -> dict[str, str]:
    rows = indicators[indicators.field_id == field_id]
    statuses = {}
    for required in ("gdd", "precipitation_total", "frost_window", "om_r_0_30cm"):
        key = "frost_free_days" if required == "frost_window" else required
        found = rows[rows.indicator_id == key]
        # Only `available` counts as known. A `partial` value is real but computed over less than the
        # whole window or area, and a comparison built on it would not be the comparison we describe.
        # This is what BE's endpoint already does; the two paths disagreed until 2026-11-15.
        statuses[required] = "ok" if len(found) and (found.status == "available").all() else "unknown"
    return statuses


def build_profiles(
    indicators: pd.DataFrame,
    fields: list[dict],
) -> list[FieldProfile]:
    latest = _latest(indicators)
    profiles = []
    for feature in fields:
        properties = feature["properties"]
        field_id = properties["field_id"]
        frost = _value(latest, field_id, "frost_free_days")
        profiles.append(
            FieldProfile(
                field_id=field_id,
                boundary_source=properties["boundary_source"],
                crop_history_summary=properties["domain_note"],
                county=properties["county"],
                crop_history_is_maize_soybean=properties["domain_note"] == IN_DOMAIN_NOTE,
                gdd_season_difference_vs_marsden=_value(
                    latest, field_id, "gdd_season_difference_vs_marsden"
                ),
                frost_free_days=UNKNOWN if frost is UNKNOWN else int(frost),
                dominant_drainage_class=_dominant_class(latest, field_id, "drainagecl_dominant"),
                indicator_statuses=_indicator_statuses(indicators, field_id),
            )
        )
    return profiles


SCENARIO_IDS = {
    "every constraint stated": "every_constraint_stated",
    "no manure": "no_manure",
    "nothing stated": "nothing_stated",
}


def outcome_row(profile: FieldProfile, scenario: str, result, run_id: str) -> dict:
    """One row of the test-set audit: a field under one constraint scenario."""
    fired = sorted(
        {finding.rule_id for outcome in result.outcomes for finding in outcome.findings}
        | {finding.rule_id for strategy in result.strategies for finding in strategy.findings}
    )
    by_status = Counter(outcome.status for outcome in result.outcomes if outcome.claimable)
    feasibility = {strategy.strategy_id: strategy.feasibility for strategy in result.strategies}
    return {
        "field_id": profile.field_id,
        "scenario": SCENARIO_IDS[scenario],
        "crop_history_summary": profile.crop_history_summary,
        "outcome": result.outcome,
        "outcome_reason": result.outcome_reason,
        "strategy_a_feasibility": feasibility.get("A", ""),
        "strategy_b_feasibility": feasibility.get("B", ""),
        "strategy_c_feasibility": feasibility.get("C", ""),
        "outcomes_in_domain": by_status.get("in_domain", 0),
        "outcomes_qualified": by_status.get("qualified", 0),
        "outcomes_abstained": by_status.get("abstained", 0),
        "outcomes_out_of_domain": by_status.get("out_of_domain", 0),
        "outcomes_not_assessed": sum(
            1 for outcome in result.outcomes if not outcome.claimable
        ),
        "rules_fired": json.dumps(fired),
        "unknowns": json.dumps(list(result.unknowns)),
        "rules_version": result.rules_version,
        "run_id": run_id,
    }


def sweep(profiles: list[FieldProfile], run_id: str = "sweep") -> dict:
    outcomes = {name: Counter() for name in SCENARIOS}
    fired = Counter()
    rows = []
    for profile in profiles:
        for name, constraints in SCENARIOS.items():
            result = assess(profile, constraints)
            outcomes[name][result.outcome] += 1
            rows.append(outcome_row(profile, name, result, run_id))
            for finding in {f.rule_id for o in result.outcomes for f in o.findings} | {
                f.rule_id for s in result.strategies for f in s.findings
            }:
                fired[finding] += 1
    never = [rule.rule_id for rule in rules.APPLICABILITY_RULES if rule.rule_id not in fired]
    return {
        "outcomes": outcomes,
        "fired": fired,
        "never_fired": never,
        "fields": len(profiles),
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--indicators", type=Path, default=INDICATORS_PATH)
    parser.add_argument("--fields", type=Path, default=FIELDS_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    if not args.indicators.exists():
        print(f"no indicator table at {args.indicators}; run transform.indicators.runner first")
        return 1

    indicators = pd.read_csv(args.indicators)
    fields = json.loads(args.fields.read_text(encoding="utf-8"))["features"]
    run_id = f"ds2-validation-{uuid.uuid4().hex[:12]}"
    result = sweep(build_profiles(indicators, fields), run_id)

    args.out.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(result["rows"])
    frame.to_csv(args.out / "engine_test_set.csv", index=False)
    manifest = {
        "run_id": run_id,
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "rules_version": rules.RULES_VERSION,
        "fields": result["fields"],
        "scenarios": sorted(SCENARIO_IDS.values()),
        "rows": len(frame),
        "rules_never_fired": result["never_fired"],
    }
    (args.out / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"{result['fields']} fields, rules version {rules.RULES_VERSION}\n")
    for name, counts in result["outcomes"].items():
        spread = ", ".join(f"{outcome} {count}" for outcome, count in sorted(counts.items()))
        print(f"  {name:<24} {spread}")

    print("\nrules that fired (any scenario):")
    for rule_id, count in result["fired"].most_common():
        print(f"  {count:>4}  {rule_id}")

    print("\nrules that never fired:")
    for rule_id in result["never_fired"]:
        print(f"        {rule_id}")
    print(f"\n  wrote {len(result['rows'])} rows to {args.out}")
    if result["never_fired"]:
        print(
            "\n  A rule that never fires is either a guardrail for input this test set does not contain,\n"
            "  or a threshold that is wrong. Both need saying out loud before the demo."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
