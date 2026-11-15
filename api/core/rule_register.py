"""Build the rule register from DS2's engine_* rows. Pure: no I/O."""
from __future__ import annotations

import json

from api.schemas.rules import (
    CropClaimOut,
    OutcomeRuleOut,
    RegisterSummaryOut,
    RuleOut,
    RuleRegisterOut,
    StrategyRuleOut,
)


def _json(text: str):
    """List and value columns are stored as JSON text. Anything that is not JSON is returned as it is."""
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return text


def _caveats(summary: RegisterSummaryOut, matches_engine: bool) -> list[str]:
    out = []
    if summary.rules_expert_reviewed == 0:
        out.append(
            "No rule has been reviewed by an agronomist. Every rule is the team's own proposal or is drawn from "
            "the Marsden Farm experiment's context."
        )
    out.append(
        f"{summary.rules_team_proposed} of {summary.rules_total} rules are team-proposed guardrails, not findings "
        "from the experiment. They decide when the engine qualifies or withholds a comparison."
    )
    if summary.claims_research_needed:
        out.append(
            f"{summary.claims_research_needed} of {summary.claims_total} crop claims have no source yet. They are "
            "listed so the gap is visible, and the engine makes no claim from them."
        )
    if not matches_engine:
        out.append(
            "The register loaded in the database is a different version from the rules the engine is running. "
            "Treat it as out of date until DS reloads it."
        )
    return out


def build_rule_register(raw: dict | None, engine_version: str, data_version: str) -> RuleRegisterOut | None:
    """None when no register has been loaded."""
    if not raw or not raw.get("rules"):
        return None
    rules = [RuleOut(**{**r, "value": _json(r["value"])}) for r in raw["rules"]]
    claims = [
        CropClaimOut(
            claim_id=c["claim_id"],
            crops=[crop.strip() for crop in c["crop"].split(",") if crop.strip()],
            claim=c["claim"], status=c["status"], evidence_type=c["evidence_type"],
            source=c["source"], note=c["note"],
        )
        for c in raw["crop_claims"]
    ]
    outcomes = [OutcomeRuleOut(**{**o, "claimable": bool(o["claimable"])}) for o in raw["outcomes"]]
    strategies = [
        StrategyRuleOut(
            **{**s, "phases": _json(s["phases"]), "operational_requirements": _json(s["operational_requirements"])}
        )
        for s in raw["strategies"]
    ]
    summary = RegisterSummaryOut(
        rules_total=len(rules),
        rules_team_proposed=sum(r.evidence_basis == "team_proposed" for r in rules),
        rules_experimental_context=sum(r.evidence_basis == "experimental_context" for r in rules),
        rules_expert_reviewed=sum(r.review == "expert_reviewed" for r in rules),
        claims_total=len(claims),
        claims_sourced=sum(c.status == "sourced" for c in claims),
        claims_research_needed=sum(c.status == "research_needed" for c in claims),
    )
    matches = raw["rules_version"] == engine_version
    return RuleRegisterOut(
        rules_version=raw["rules_version"], engine_version=engine_version, matches_engine=matches,
        summary=summary, rules=rules, crop_claims=claims, outcomes=outcomes, strategies=strategies,
        caveats=_caveats(summary, matches), data_version=data_version,
    )
