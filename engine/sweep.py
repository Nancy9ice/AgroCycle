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
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from engine.decision import UNKNOWN, FarmerConstraints, FieldProfile, assess
from engine.rules import strategy_rules as rules

REPO_ROOT = Path(__file__).resolve().parents[1]
INDICATORS_PATH = REPO_ROOT / "data" / "out" / "indicators" / "field_indicators.csv"
FIELDS_PATH = REPO_ROOT / "data" / "fields" / "fields.geojson"
IN_DOMAIN_NOTE = "in-domain: maize-soybean rotation"
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
        statuses[required] = "ok" if len(found) and (found.status != "unknown").all() else "unknown"
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


def sweep(profiles: list[FieldProfile]) -> dict:
    outcomes = {name: Counter() for name in SCENARIOS}
    fired = Counter()
    for profile in profiles:
        for name, constraints in SCENARIOS.items():
            result = assess(profile, constraints)
            outcomes[name][result.outcome] += 1
            for finding in {f.rule_id for o in result.outcomes for f in o.findings} | {
                f.rule_id for s in result.strategies for f in s.findings
            }:
                fired[finding] += 1
    never = [rule.rule_id for rule in rules.APPLICABILITY_RULES if rule.rule_id not in fired]
    return {"outcomes": outcomes, "fired": fired, "never_fired": never, "fields": len(profiles)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--indicators", type=Path, default=INDICATORS_PATH)
    parser.add_argument("--fields", type=Path, default=FIELDS_PATH)
    args = parser.parse_args(argv)

    if not args.indicators.exists():
        print(f"no indicator table at {args.indicators}; run transform.indicators.runner first")
        return 1

    indicators = pd.read_csv(args.indicators)
    fields = json.loads(args.fields.read_text(encoding="utf-8"))["features"]
    result = sweep(build_profiles(indicators, fields))

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
    if result["never_fired"]:
        print(
            "\n  A rule that never fires is either a guardrail for input this test set does not contain,\n"
            "  or a threshold that is wrong. Both need saying out loud before the demo."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
