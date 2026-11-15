"""Strategy profiles, crop characteristics and outcome-specific applicability rules.

AgroCycle, DS2, roadmap Phase 9. The rule table the Phase 10 decision engine evaluates. This module holds
**data and a renderer only**: it decides nothing, so that the rules can be reviewed by someone who does not
read Python, in ``docs/rules/strategy-profiles-and-applicability.md``, which is generated from here.

Three things it is careful about:

* **Applicability is per outcome, never per strategy.** PRD 7.6: no manure access limits the transfer of the
  manure-dependent nitrogen comparison but does not invalidate the herbicide comparison. Every rule names one
  ``outcome_id``.
* **Unsourced agronomy is marked, not written.** PRD 7.5: where a crop-characteristic source is not
  identified, the explanation is a research requirement, not an invented value. Claims that Davis et al.
  (2012) and its supplement do not support carry ``status="research_needed"`` and name the kind of source that
  would settle them.
* **Outcomes that must never be claimed are present and closed.** Soil carbon, measured erosion and nitrate
  leaching appear with ``claimable=False``, so the engine returns an explicit "not assessed" rather than
  leaving a gap a later contributor might fill.

Every rule here is a conservative team-proposed guardrail and is **not expert-reviewed** (PRD 7.6).

Regenerate the document from the repository root:

    python -m engine.rules.strategy_rules
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

RULES_VERSION = "2026-11-15.4"

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_PATH = REPO_ROOT / "docs" / "rules" / "strategy-profiles-and-applicability.md"

EVIDENCE_TYPES = (
    "observed",
    "derived",
    "classified",
    "survey",
    "model_reanalysis",
    "experimental",
    "published",
    "assumption",
)
DECISION_OUTCOMES = ("strategy_worth_exploring", "qualified_comparison", "abstention")
RULE_EFFECTS = ("in_domain", "qualified", "out_of_domain", "abstain_outcome")
CLAIM_STATUSES = ("sourced", "research_needed")
OPERATORS = (
    "equals",
    "not_equals",
    "lt",
    "lte",
    "gt",
    "gte",
    "in",
    "not_in",
    "is_unknown",
)
REVIEW_STATUSES = ("not_expert_reviewed", "expert_reviewed")

MARSDEN_PAPER = "Davis et al. (2012), PLOS ONE 7(10): e47149 [S09]"
MARSDEN_SUPPLEMENT = "Davis et al. (2012) supplementary management records [S10]"
OUR_REPRODUCTION = "AgroCycle reproduction, transform/marsden (roadmap Phase 6)"
RESEARCH_NEEDED_NOTE = (
    "No agronomic source retrieved yet. Needs a citable source (for example Iowa State University Extension "
    "agronomy guidance or peer-reviewed Iowa rotation literature) before this is shown as an explanation."
)


@dataclass(frozen=True)
class StrategyProfile:
    strategy_id: str
    label: str
    rotation: str
    phases: tuple[str, ...]
    why_included: str
    operational_requirements: tuple[str, ...]
    evidence_anchor: str


@dataclass(frozen=True)
class OutcomeEvidence:
    outcome_id: str
    label: str
    claimable: bool
    evidence_type: str | None
    source: str | None
    statement: str
    caution: str
    caution_reference: str


@dataclass(frozen=True)
class CropClaim:
    claim_id: str
    crop: str
    claim: str
    status: str
    evidence_type: str | None
    source: str | None
    note: str


@dataclass(frozen=True)
class ApplicabilityRule:
    rule_id: str
    outcome_id: str
    context_key: str
    operator: str
    value: object
    effect: str
    condition_text: str
    rationale: str
    evidence_basis: str
    review: str = "not_expert_reviewed"


STRATEGY_PROFILES = (
    StrategyProfile(
        strategy_id="A",
        label="Existing system",
        rotation="Two-year maize-soybean",
        phases=("maize", "soybean"),
        why_included=(
            "The baseline the farmer already runs and the system every comparison is measured against."
        ),
        operational_requirements=(
            "Equipment and markets already in place for maize and soybean",
            "Nitrogen purchased as manufactured fertiliser",
        ),
        evidence_anchor=f"Two-year treatment of the Marsden Farm experiment, {MARSDEN_PAPER}",
    ),
    StrategyProfile(
        strategy_id="B",
        label="Diversified option",
        rotation="Three-year maize-soybean-oat/red clover",
        phases=("maize", "soybean", "oat_red_clover"),
        why_included=(
            "Adds a small-grain and a forage-legume phase, the shortest diversification the Marsden "
            "experiment tested."
        ),
        operational_requirements=(
            "A use or buyer for oat grain and straw",
            "Red clover establishment, usually frost-seeded into the small grain",
            "Manure access: the Marsden three-year system received composted manure",
            "Equipment and labour for small-grain harvest",
        ),
        evidence_anchor=f"Three-year treatment of the Marsden Farm experiment, {MARSDEN_PAPER}",
    ),
    StrategyProfile(
        strategy_id="C",
        label="Diversified option",
        rotation="Four-year maize-soybean-oat/alfalfa-alfalfa",
        phases=("maize", "soybean", "oat_alfalfa", "alfalfa"),
        why_included=(
            "Adds a small grain and two years of a perennial forage legume, the longest rotation the Marsden "
            "experiment tested."
        ),
        operational_requirements=(
            "A forage use or buyer for alfalfa across two years of the rotation",
            "Alfalfa establishment, multiple cuts per season, and storage or handling for forage",
            "Manure access: the Marsden four-year system received composted manure",
            "Equipment and labour for small-grain and forage harvest",
            "Commitment to keep a quarter of the land out of maize and soybean for two years at a time",
        ),
        evidence_anchor=f"Four-year treatment of the Marsden Farm experiment, {MARSDEN_PAPER}",
    ),
)

OUTCOME_EVIDENCE = (
    OutcomeEvidence(
        outcome_id="applied_n_reduction",
        label="Lower applied nitrogen (manufactured plus manure)",
        claimable=True,
        evidence_type="experimental",
        source=f"{MARSDEN_SUPPLEMENT}; reproduced in {OUR_REPRODUCTION}",
        statement=(
            "In the Marsden experiment, nine-year applied N averaged 74.5, 56.6 and 40.8 kg N/ha/yr for the "
            "two-, three- and four-year systems, and manufactured N alone was 74.5, 16.7 and 10.9. These are "
            "rotation-area-weighted averages from one site over nine seasons."
        ),
        caution=(
            "These figures come from one research farm over nine seasons, so they are not a prediction for "
            "your field. The diversified systems also received manure, so this is not a drop in the nitrogen "
            "the crop received, and it leaves out the nitrogen the clover and alfalfa fix themselves."
        ),
        caution_reference="Davis et al. (2012), supplementary records",
    ),
    OutcomeEvidence(
        outcome_id="herbicide_reduction",
        label="Lower herbicide active ingredient per hectare per year",
        claimable=True,
        evidence_type="experimental",
        source=f"{MARSDEN_SUPPLEMENT}; reproduced in {OUR_REPRODUCTION}",
        statement=(
            "In the Marsden experiment, herbicide active ingredient averaged 1.925, 0.261 and 0.195 "
            "kg ai/ha/yr for the two-, three- and four-year systems, about 86-90 % lower in the diversified "
            "systems."
        ),
        caution=(
            "This is the weight of herbicide applied, which says nothing about how harmful it is or who was "
            "exposed to it. Insecticides used in 2007 to 2009 are not counted. One research farm over nine "
            "seasons is not a prediction for your field."
        ),
        caution_reference="Davis et al. (2012), supplementary records",
    ),
    OutcomeEvidence(
        outcome_id="yield_parity",
        label="Maize and soybean yields matched or exceeded the two-year system",
        claimable=True,
        evidence_type="published",
        source=MARSDEN_PAPER,
        statement=(
            "The publication reports that maize and soybean yields in the diversified systems matched or "
            "exceeded the two-year system. This is attributed to the paper."
        ),
        caution=(
            "This is the researchers' own published result. We have not recalculated it, because the data "
            "they published does not include the field-by-field yields. It does not predict what your field "
            "would yield."
        ),
        caution_reference="Davis et al. (2012)",
    ),
    OutcomeEvidence(
        outcome_id="profitability_parity",
        label="No significant difference in net returns between systems",
        claimable=True,
        evidence_type="published",
        source=MARSDEN_PAPER,
        statement=(
            "The publication reports no significant difference in net returns between the systems, under its "
            "own price and cost assumptions."
        ),
        caution=(
            "This was true at their prices and costs, on their farm. AgroCycle does not work out profit: "
            "that would need your yields, input costs, machinery, labour, transport and prices, and we have "
            "none of them."
        ),
        caution_reference="Davis et al. (2012); AgroCycle scope (PRD section 9)",
    ),
    OutcomeEvidence(
        outcome_id="weed_suppression",
        label="Weed suppression in the diversified systems",
        claimable=True,
        evidence_type="published",
        source=MARSDEN_PAPER,
        statement=(
            "The publication reports its own weed findings, which are attributed to it and not recomputed."
        ),
        caution=(
            "The records we reproduced cover herbicide applied, not weed numbers. The weed findings are the "
            "researchers' own and do not predict weed pressure on your field."
        ),
        caution_reference="Davis et al. (2012)",
    ),
    OutcomeEvidence(
        outcome_id="soil_carbon_change",
        label="Soil carbon gain",
        claimable=False,
        evidence_type=None,
        source=None,
        statement="Not assessed.",
        caution=(
            "Nothing AgroCycle uses measures soil carbon on a field, and the experiment's records do not "
            "show a soil-carbon gain. Shown as not assessed."
        ),
        caution_reference="PRD section 7.4 and 4.4",
    ),
    OutcomeEvidence(
        outcome_id="erosion_reduction",
        label="Measured erosion reduction",
        claimable=False,
        evidence_type=None,
        source=None,
        statement="Not assessed.",
        caution=(
            "Nothing AgroCycle uses measures erosion on a field. Estimating it would need a method the team "
            "has not agreed, so it is shown as not assessed."
        ),
        caution_reference="PRD section 7.4",
    ),
    OutcomeEvidence(
        outcome_id="nitrate_leaching_reduction",
        label="Measured nitrate-leaching reduction",
        claimable=False,
        evidence_type=None,
        source=None,
        statement="Not assessed.",
        caution=(
            "Applying less nitrogen is not the same as measuring less nitrate leaving the soil. Nothing "
            "AgroCycle uses measures leaching, so it is shown as not assessed."
        ),
        caution_reference="PRD section 7.4",
    ),
    OutcomeEvidence(
        outcome_id="forage_supply",
        label="Forage produced for on-farm use or sale",
        claimable=False,
        evidence_type=None,
        source=None,
        statement="Not assessed.",
        caution=(
            "We have no figures for forage yield, quality or feed value: no source found yet. That the "
            "four-year rotation grows alfalfa for two years is part of how the rotation is defined, not a "
            "measured amount of feed."
        ),
        caution_reference="no source found yet",
    ),
)

STRATEGY_FEASIBILITY_TARGETS = ("strategy_b_feasibility", "strategy_c_feasibility")
WHOLE_COMPARISON_TARGET = "all_outcomes"
RULE_TARGETS = (
    tuple(outcome.outcome_id for outcome in OUTCOME_EVIDENCE)
    + STRATEGY_FEASIBILITY_TARGETS
    + (WHOLE_COMPARISON_TARGET,)
)

CROP_CLAIMS = (
    CropClaim(
        claim_id="marsden_manure_to_diversified",
        crop="red_clover, alfalfa",
        claim=(
            "The Marsden three- and four-year systems received composted manure, so their nitrogen "
            "comparison depends on manure being available."
        ),
        status="sourced",
        evidence_type="experimental",
        source=f"{MARSDEN_SUPPLEMENT}; reproduced in {OUR_REPRODUCTION}",
        note=(
            "Manure N is total N in composted manure, not plant-available N. Text S1 places the application "
            "on the clover and alfalfa phases."
        ),
    ),
    CropClaim(
        claim_id="legume_biological_fixation",
        crop="red_clover, alfalfa",
        claim="Legumes may contribute biologically fixed nitrogen under suitable conditions.",
        status="research_needed",
        evidence_type=None,
        source=None,
        note=(
            f"PRD 7.5 names this as an example of a potential mechanism, not a measured outcome for a field. "
            f"{RESEARCH_NEEDED_NOTE} The magnitude depends on species, establishment, management, soil and "
            "climate, and the Marsden applied-N figures exclude fixation entirely."
        ),
    ),
    CropClaim(
        claim_id="living_cover_bare_periods",
        crop="oat, red_clover, alfalfa",
        claim="A small grain or forage phase may provide living cover during otherwise bare periods.",
        status="research_needed",
        evidence_type=None,
        source=None,
        note=(
            f"Listed in PRD 7.5 as a potential mechanism. {RESEARCH_NEEDED_NOTE} DS1's bare-field windows "
            "(Phase 5) could show cover timing for a field, but that is an observation of this field, not "
            "evidence that the rotation causes it."
        ),
    ),
    CropClaim(
        claim_id="rooting_depth_soil_structure",
        crop="alfalfa",
        claim="Deeper or different rooting patterns may affect soil structure.",
        status="research_needed",
        evidence_type=None,
        source=None,
        note=f"Listed in PRD 7.5 as a potential mechanism. {RESEARCH_NEEDED_NOTE}",
    ),
    CropClaim(
        claim_id="forage_feed_value",
        crop="alfalfa, oat",
        claim="Forage crops may provide feed value.",
        status="research_needed",
        evidence_type=None,
        source=None,
        note=(
            f"Listed in PRD 7.5 as a potential mechanism. {RESEARCH_NEEDED_NOTE} No forage yield or quality "
            "figure is available from any AgroCycle source."
        ),
    ),
    CropClaim(
        claim_id="alfalfa_drainage_sensitivity",
        crop="alfalfa",
        claim="Alfalfa is sensitive to poor drainage and waterlogging.",
        status="research_needed",
        evidence_type=None,
        source=None,
        note=(
            f"{RESEARCH_NEEDED_NOTE} An applicability rule for alfalfa on poorly drained soil was withdrawn on "
            "2026-11-15 because this claim had no source. The drainage composition is still shown to "
            "the farmer as survey data; what was removed is our inference from it."
        ),
    ),
    CropClaim(
        claim_id="oat_season_window",
        crop="oat",
        claim="Oat needs an early-spring planting window and matures mid-season.",
        status="research_needed",
        evidence_type=None,
        source=None,
        note=(
            f"{RESEARCH_NEEDED_NOTE} An applicability rule using a 120-day frost-free threshold was withdrawn on "
            "2026-11-15: it had no source, and the shortest frost-free window measured across the 45 "
            "fields was 159 days, so it could never have fired."
        ),
    ),
    CropClaim(
        claim_id="rotation_disease_pest_effects",
        crop="maize, soybean, oat, red_clover, alfalfa",
        claim="Rotation length may affect disease and pest pressure.",
        status="research_needed",
        evidence_type=None,
        source=None,
        note=(
            f"{RESEARCH_NEEDED_NOTE} Until sourced, the disease and pest dimension of the comparison is "
            "reported as not assessed rather than left blank."
        ),
    ),
)

APPLICABILITY_RULES = (
    ApplicabilityRule(
        rule_id="applicability_manure_access_applied_n",
        outcome_id="applied_n_reduction",
        context_key="manure_access",
        operator="equals",
        value=False,
        effect="out_of_domain",
        condition_text="The farmer has no access to manure.",
        rationale=(
            "Manure supplied 39.9 and 29.9 kg N/ha/yr of the three- and four-year systems' applied nitrogen. "
            "Without manure the diversified systems as tested at Marsden cannot be reproduced, so the applied "
            "nitrogen comparison does not transfer."
        ),
        evidence_basis="experimental_context",
    ),
    ApplicabilityRule(
        rule_id="applicability_manure_unknown_applied_n",
        outcome_id="applied_n_reduction",
        context_key="manure_access",
        operator="is_unknown",
        value=None,
        effect="abstain_outcome",
        condition_text="Manure access has not been stated.",
        rationale=(
            "Missing data is not evidence of access (PRD 8.5). The outcome is withheld until the farmer says, "
            "rather than assumed either way."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_crop_history_baseline",
        outcome_id="all_outcomes",
        context_key="crop_history_is_maize_soybean",
        operator="equals",
        value=False,
        effect="out_of_domain",
        condition_text="The field's recent crop history is not a maize-soybean rotation.",
        rationale=(
            "Every Marsden comparison is measured against a two-year maize-soybean baseline. A field in "
            "continuous maize, pasture or a non-rotation sequence is outside the experiment's domain, so the "
            "comparison is not offered for it."
        ),
        evidence_basis="experimental_context",
    ),
    ApplicabilityRule(
        rule_id="applicability_crop_history_unknown",
        outcome_id="all_outcomes",
        context_key="crop_history_is_maize_soybean",
        operator="is_unknown",
        value=None,
        effect="abstain_outcome",
        condition_text="Crop history could not be classified.",
        rationale=(
            "A field whose CDL history is unavailable or low-confidence cannot be placed in or out of the "
            "domain, so the engine abstains rather than assuming the baseline."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_outside_demo_counties",
        outcome_id="all_outcomes",
        context_key="county",
        operator="not_in",
        value=("Story", "Boone"),
        effect="qualified",
        condition_text="The field lies outside Story or Boone County, Iowa.",
        rationale=(
            "The MVP's soil, climate and validation resources were assembled for these two counties (PRD "
            "2.3). A field elsewhere is not excluded, but the comparison is qualified because the supporting "
            "context was not assembled for it."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_forage_outlet_strategy_c",
        outcome_id="strategy_c_feasibility",
        context_key="forage_use_or_buyer",
        operator="equals",
        value=False,
        effect="out_of_domain",
        condition_text="There is no on-farm forage use and no buyer for alfalfa.",
        rationale=(
            "The four-year rotation grows alfalfa for two years of four. With no use and no buyer the "
            "rotation is not operationally available, whatever the environmental evidence says (PRD 9)."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_oat_outlet_strategy_b",
        outcome_id="strategy_b_feasibility",
        context_key="oat_use_or_buyer",
        operator="equals",
        value=False,
        effect="qualified",
        condition_text="There is no on-farm use and no buyer for oat grain or straw.",
        rationale=(
            "A single small-grain phase with no outlet is a real feasibility problem but a smaller commitment "
            "than two years of alfalfa, so it qualifies the option rather than removing it (PRD 9)."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_machinery_small_grain",
        outcome_id="strategy_b_feasibility",
        context_key="small_grain_equipment_or_contractor",
        operator="equals",
        value=False,
        effect="qualified",
        condition_text="Neither small-grain equipment nor a contractor is available.",
        rationale=(
            "Equipment and labour for small-grain harvest are an operational requirement of both diversified "
            "options and a first-class constraint, not explanatory text (PRD 9)."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_forage_outlet_unknown",
        outcome_id="strategy_c_feasibility",
        context_key="forage_use_or_buyer",
        operator="is_unknown",
        value=None,
        effect="qualified",
        condition_text="Whether there is a forage use or buyer has not been stated.",
        rationale=(
            "An unstated outlet is not an available one. The option is shown with the question attached "
            "rather than treated as operationally settled (PRD 8.5)."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_oat_outlet_unknown",
        outcome_id="strategy_b_feasibility",
        context_key="oat_use_or_buyer",
        operator="is_unknown",
        value=None,
        effect="qualified",
        condition_text="Whether there is an oat use or buyer has not been stated.",
        rationale=(
            "An unstated outlet is not an available one; the option is qualified until the farmer says "
            "(PRD 8.5)."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_machinery_unknown",
        outcome_id="strategy_b_feasibility",
        context_key="small_grain_equipment_or_contractor",
        operator="is_unknown",
        value=None,
        effect="qualified",
        condition_text="Small-grain equipment or contractor access has not been stated.",
        rationale=(
            "Unstated machinery access is not assumed access. Both diversified options need small-grain "
            "harvest, so the question is carried into the comparison (PRD 8.5, 9)."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_machinery_small_grain_strategy_c",
        outcome_id="strategy_c_feasibility",
        context_key="small_grain_equipment_or_contractor",
        operator="equals",
        value=False,
        effect="qualified",
        condition_text="Neither small-grain equipment nor a contractor is available.",
        rationale=(
            "The four-year rotation has an oat phase too, and its own operational requirements list "
            "equipment and labour for small-grain and forage harvest. Added 2026-11-15 after the "
            "validation matrix showed the machinery rules qualified the three-year option while leaving "
            "the four-year one untouched, which their rationale never intended."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_machinery_unknown_strategy_c",
        outcome_id="strategy_c_feasibility",
        context_key="small_grain_equipment_or_contractor",
        operator="is_unknown",
        value=None,
        effect="qualified",
        condition_text="Small-grain equipment or contractor access has not been stated.",
        rationale=(
            "Unstated machinery access is not assumed access, for the four-year option as much as the "
            "three-year one (PRD 8.5, 9)."
        ),
        evidence_basis="team_proposed",
    ),
    ApplicabilityRule(
        rule_id="applicability_indicator_coverage",
        outcome_id="all_outcomes",
        context_key="required_indicators_all_known",
        operator="equals",
        value=False,
        effect="abstain_outcome",
        condition_text="One or more required profile indicators came back unknown.",
        rationale=(
            "PRD 8.5: missing data is never evidence of no risk or no benefit. An indicator that returned "
            "'unknown' withholds the dimensions that depend on it instead of being read as neutral."
        ),
        evidence_basis="team_proposed",
    ),
)


def _markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def render_markdown() -> str:
    """Render the rule table as the reviewable document. Generated: never edit the output by hand."""
    lines = [
        "# AgroCycle strategy profiles and applicability rules",
        "",
        f"**Rules version:** {RULES_VERSION}  ",
        "**Role:** DS2, roadmap Phase 9  ",
        ("**Review status: NOT EXPERT-REVIEWED.** Every rule below is a conservative team-proposed guardrail, "
        "not a universal agronomic threshold (PRD 7.6)."),
        "",
        "> This file is **generated** from `engine/rules/strategy_rules.py`. Edit the module, then run",
        "> `python -m engine.rules.strategy_rules` from the repository root. A test fails if the two differ.",
        "",
        "The Phase 10 decision engine evaluates these rules. This table decides nothing by itself.",
        "",
        "## 1. Strategy profiles",
        "",
    ]
    for profile in STRATEGY_PROFILES:
        lines.extend(
            [
                f"### {profile.strategy_id} — {profile.label}: {profile.rotation}",
                "",
                f"- **Phases:** {', '.join(profile.phases)}",
                f"- **Why included:** {profile.why_included}",
                f"- **Evidence anchor:** {profile.evidence_anchor}",
                "- **Operational requirements:**",
            ]
        )
        lines.extend(f"  - {requirement}" for requirement in profile.operational_requirements)
        lines.append("")

    lines.extend(
        [
            "## 2. Outcomes: what may and may not be said",
            "",
            ("An outcome marked **not claimable** must be reported as unknown / not assessed. It is listed so "
            "the engine has something explicit to return."),
            "",
        ]
    )
    for outcome in OUTCOME_EVIDENCE:
        claimable = "claimable" if outcome.claimable else "**NOT claimable**"
        evidence = outcome.evidence_type or "none"
        lines.extend(
            [
                f"### {outcome.outcome_id} — {outcome.label}",
                "",
                f"- **Status:** {claimable} · evidence type: `{evidence}`",
                f"- **Source:** {outcome.source or 'none'}",
                f"- **May be said:** {outcome.statement}",
                f"- **Caution shown to the farmer:** {outcome.caution}",
                f"- **Caution source line:** {outcome.caution_reference}",
                "",
            ]
        )

    sourced = [claim for claim in CROP_CLAIMS if claim.status == "sourced"]
    research = [claim for claim in CROP_CLAIMS if claim.status == "research_needed"]
    lines.extend(
        [
            "## 3. Crop characteristics",
            "",
            (f"{len(sourced)} of {len(CROP_CLAIMS)} claims are sourced. The rest are marked "
            "**research needed** and must not be shown as explanations until a citable source exists "
            "(PRD 7.5). They are listed rather than omitted so the gap is visible."),
            "",
            "### Sourced",
            "",
        ]
    )
    lines.extend(
        _markdown_table(
            ["Claim id", "Crop", "Claim", "Evidence", "Source", "Note"],
            [
                [
                    claim.claim_id,
                    claim.crop,
                    claim.claim,
                    f"`{claim.evidence_type}`",
                    claim.source or "",
                    claim.note,
                ]
                for claim in sourced
            ],
        )
    )
    lines.extend(["", "### Research needed", ""])
    lines.extend(
        _markdown_table(
            ["Claim id", "Crop", "Claim", "What is needed"],
            [[claim.claim_id, claim.crop, claim.claim, claim.note] for claim in research],
        )
    )

    lines.extend(
        [
            "",
            "## 4. Outcome-specific applicability rules",
            "",
            ("Applicability is assessed **per outcome**, never per strategy: lack of manure access limits the "
            "manure-dependent nitrogen comparison but does not invalidate the herbicide comparison "
            "(PRD 7.6). `all_outcomes` means the rule applies to the whole comparison."),
            "",
            ("Effects: `in_domain`, `qualified` (show it, with the reason), `out_of_domain` (do not offer it), "
            "`abstain_outcome` (withhold pending data)."),
            "",
        ]
    )
    lines.extend(
        _markdown_table(
            ["Rule id", "Outcome", "Condition", "Effect", "Basis", "Rationale"],
            [
                [
                    rule.rule_id,
                    f"`{rule.outcome_id}`",
                    f"{rule.condition_text} (`{rule.context_key}` {rule.operator} `{rule.value}`)",
                    f"**{rule.effect}**",
                    rule.evidence_basis,
                    rule.rationale,
                ]
                for rule in APPLICABILITY_RULES
            ],
        )
    )

    lines.extend(
        [
            "",
            "## 5. Permitted decision outcomes (PRD 8.3)",
            "",
            "| Outcome | When it is appropriate |",
            "|---|---|",
            ("| `strategy_worth_exploring` | Evidence and the farmer's priorities make the option a reasonable "
            "candidate for further local evaluation. Not a prescription. |"),
            ("| `qualified_comparison` | Evidence supports comparing strategies but is insufficient to identify "
            "a preferred option. |"),
            ("| `abstention` | Evidence is missing, inadequate, contradictory, or outside the supported "
            "applicability domain. |"),
            "",
            "The engine must not force a ranking because a user expects one.",
            "",
            "## 6. Known weaknesses of this table",
            "",
            ("- No rule has been reviewed by an agricultural expert. The roadmap asks for review by an "
            "Iowa-knowledgeable adviser; the farmer reviewer is Nigerian and can sanity-check practicality "
            "(machinery, labour, markets) but not Iowa agronomy."),
            ("- **Climate transferability is not assessed.** The rule that compared a field's growing-season "
            "heat with the Marsden site's was withdrawn on 2026-11-15: its 300 degree-day band had no "
            "published basis, and across the 45 test fields the largest difference measured was 43, so it "
            "could never fire. A guardrail that cannot trigger gives false assurance that the question was "
            "asked. Transferability is still assessed on crop history, county and manure access."),
            ("- Two rules that rested on unsourced crop claims (alfalfa on poorly drained soil, and an oat "
            "season-length threshold) were withdrawn on 2026-11-15. No rule now depends on a claim marked "
            "research needed, and a test enforces that."),
            ("- A rule carries one condition, so interactions between conditions cannot be expressed. If "
            "review shows interactions matter, Phase 10 needs a richer form."),
            ("- Most crop characteristics are unsourced, so the \"why this crop\" explanation is thin by "
            "design rather than complete."),
        ]
    )
    return "\n".join(lines) + "\n"


def write_document(path: Path = DOCUMENT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(), encoding="utf-8")
    return path


if __name__ == "__main__":
    written = write_document()
    print(f"wrote {written.relative_to(REPO_ROOT)} (rules version {RULES_VERSION})")
    sys.exit(0)
