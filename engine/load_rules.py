"""Load the rule table into ClickHouse so the API can read it (AgroCycle, DS2, roadmap Phase 9/10).

`engine/rules/strategy_rules.py` stays the source of truth. This copies it into four tables so BE does not
have to import Python or parse the frontend's generated JSON:

* `engine_rules`        — the applicability rules, one row each
* `engine_outcomes`     — what may and may not be said per outcome, with the farmer-facing caution
* `engine_crop_claims`  — the evidence register: which crop claims are sourced and which are not
* `engine_strategies`   — the three strategies, their phases and operational requirements

Every row carries `rules_version`. A load replaces the rows for that version rather than appending, so
re-running is safe and older versions stay for history. Readers must pick the newest version by
`loaded_at` rather than `max(rules_version)`, which is a string comparison and would put `.9` above
`.10`.

List-valued columns are JSON strings, matching how `indicator_lineage` already stores `variables`.

Usage from the repository root:

    uv run python -m engine.load_rules          # dry run
    uv run python -m engine.load_rules --yes    # create if needed, then load
"""
from __future__ import annotations

import argparse
import json
import sys

from engine.load_test_set import client
from engine.rules import strategy_rules as rules

DDL = {
    "engine_rules": """
CREATE TABLE IF NOT EXISTS engine_rules (
    rule_id         String,
    applies_to      String,
    context_key     LowCardinality(String),
    operator        LowCardinality(String),
    value           String,
    effect          Enum8('in_domain' = 1, 'qualified' = 2, 'out_of_domain' = 3, 'abstain_outcome' = 4),
    condition_text  String,
    rationale       String,
    evidence_basis  Enum8('experimental_context' = 1, 'team_proposed' = 2),
    review          Enum8('not_expert_reviewed' = 1, 'expert_reviewed' = 2),
    rules_version   LowCardinality(String),
    loaded_at       DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree ORDER BY (rules_version, rule_id)
""",
    "engine_outcomes": """
CREATE TABLE IF NOT EXISTS engine_outcomes (
    outcome_id        String,
    label             String,
    claimable         UInt8,
    evidence_type     LowCardinality(String),
    source            String,
    statement         String,
    caution           String,
    caution_reference String,
    rules_version     LowCardinality(String),
    loaded_at         DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree ORDER BY (rules_version, outcome_id)
""",
    "engine_crop_claims": """
CREATE TABLE IF NOT EXISTS engine_crop_claims (
    claim_id      String,
    crop          String,
    claim         String,
    status        Enum8('sourced' = 1, 'research_needed' = 2),
    evidence_type LowCardinality(String),
    source        String,
    note          String,
    rules_version LowCardinality(String),
    loaded_at     DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree ORDER BY (rules_version, claim_id)
""",
    "engine_strategies": """
CREATE TABLE IF NOT EXISTS engine_strategies (
    strategy_id             String,
    label                   String,
    rotation                String,
    phases                  String,
    why_included            String,
    operational_requirements String,
    evidence_anchor         String,
    rules_version           LowCardinality(String),
    loaded_at               DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree ORDER BY (rules_version, strategy_id)
""",
}


def rule_rows(version: str) -> list[dict]:
    return [
        {
            "rule_id": rule.rule_id,
            # 'all_outcomes' and the strategy_*_feasibility targets are not outcome ids, hence applies_to.
            "applies_to": rule.outcome_id,
            "context_key": rule.context_key,
            "operator": rule.operator,
            "value": json.dumps(rule.value),
            "effect": rule.effect,
            "condition_text": rule.condition_text,
            "rationale": rule.rationale,
            "evidence_basis": rule.evidence_basis,
            "review": rule.review,
            "rules_version": version,
        }
        for rule in rules.APPLICABILITY_RULES
    ]


def outcome_rows(version: str) -> list[dict]:
    return [
        {
            "outcome_id": outcome.outcome_id,
            "label": outcome.label,
            "claimable": 1 if outcome.claimable else 0,
            "evidence_type": outcome.evidence_type or "",
            "source": outcome.source or "",
            "statement": outcome.statement,
            "caution": outcome.caution,
            "caution_reference": outcome.caution_reference,
            "rules_version": version,
        }
        for outcome in rules.OUTCOME_EVIDENCE
    ]


def claim_rows(version: str) -> list[dict]:
    return [
        {
            "claim_id": claim.claim_id,
            "crop": claim.crop,
            "claim": claim.claim,
            "status": claim.status,
            "evidence_type": claim.evidence_type or "",
            "source": claim.source or "",
            "note": claim.note,
            "rules_version": version,
        }
        for claim in rules.CROP_CLAIMS
    ]


def strategy_rows(version: str) -> list[dict]:
    return [
        {
            "strategy_id": profile.strategy_id,
            "label": profile.label,
            "rotation": profile.rotation,
            "phases": json.dumps(list(profile.phases)),
            "why_included": profile.why_included,
            "operational_requirements": json.dumps(list(profile.operational_requirements)),
            "evidence_anchor": profile.evidence_anchor,
            "rules_version": version,
        }
        for profile in rules.STRATEGY_PROFILES
    ]


BUILDERS = {
    "engine_rules": rule_rows,
    "engine_outcomes": outcome_rows,
    "engine_crop_claims": claim_rows,
    "engine_strategies": strategy_rows,
}


def load(connection, version: str) -> dict[str, int]:
    loaded = {}
    for table, build in BUILDERS.items():
        connection.command(DDL[table])
        connection.command(
            f"ALTER TABLE {table} DELETE WHERE rules_version = %(v)s", parameters={"v": version}
        )
        rows = build(version)
        columns = list(rows[0])
        connection.insert(table, [[row[c] for c in columns] for row in rows], column_names=columns)
        loaded[table] = len(rows)
    return loaded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="actually create and load")
    args = parser.parse_args(argv)

    version = rules.RULES_VERSION
    counts = {table: len(build(version)) for table, build in BUILDERS.items()}
    print(f"rules version {version}")
    for table, count in counts.items():
        print(f"  {table:<22}{count:>4} rows")

    if not args.yes:
        print("\ndry run; nothing written. Re-run with --yes.")
        return 0

    connection = client()
    loaded = load(connection, version)
    print()
    for table, count in loaded.items():
        total = connection.query(f"SELECT count() FROM {table}").result_rows[0][0]
        print(f"  loaded {count:>3} into {table:<22} (table now holds {total})")

    unsourced = connection.query(
        "SELECT count() FROM engine_crop_claims "
        "WHERE status = 'research_needed' AND rules_version = %(v)s",
        parameters={"v": version},
    ).result_rows[0][0]
    unreviewed = connection.query(
        "SELECT count() FROM engine_rules WHERE review = 'not_expert_reviewed' "
        "AND rules_version = %(v)s",
        parameters={"v": version},
    ).result_rows[0][0]
    print(f"\n  {unsourced} crop claims are research_needed and {unreviewed} rules are not expert-reviewed.")
    print("  Anything shown to a farmer from these tables must carry that.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
