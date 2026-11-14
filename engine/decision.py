"""Deterministic decision engine (AgroCycle, DS2 with DS1, roadmap Phase 10).

Takes a field profile and the farmer's constraints and returns one of the three outcomes PRD 8.3 permits:
``strategy_worth_exploring``, ``qualified_comparison`` or ``abstention``. Pure functions, no I/O, no network,
no randomness: the same inputs always give the same result.

All policy lives in ``engine.rules.strategy_rules``; this module only evaluates it. Nothing here decides what
the evidence says, which strategy is better, or whether a claim is allowed.

Three properties the tests pin:

* **Unknown is not false.** ``UNKNOWN`` is a distinct sentinel. A condition such as
  ``manure_access equals False`` fires only when the farmer has said no; when they have said nothing, the
  matching ``is_unknown`` rule fires instead and the outcome is withheld. Missing data is never read as
  favourable (PRD 8.5).
* **No ranking, no score.** The result carries no winner, no weighting and no composite number. PRD 8.4 says
  it must be possible to return a comparison without a winner, and 8.5 forbids a composite score unless its
  components, weights and sensitivity are explicit.
* **Forbidden claims stay forbidden.** An outcome the rule table marks ``claimable=False`` is returned as
  ``not_assessed`` whatever the rules produce, so soil carbon, erosion and nitrate leaching cannot reappear
  through the engine.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field

from engine.rules import strategy_rules as rules


class _Unknown:
    """Sentinel for a value nobody has established. Distinct from False and from None."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNKNOWN"

    def __bool__(self) -> bool:
        raise TypeError("UNKNOWN has no truth value; test it with 'is UNKNOWN'")


UNKNOWN = _Unknown()

SEVERITY = ("in_domain", "qualified", "abstain_outcome", "out_of_domain")

OUTCOME_STATUS_FROM_EFFECT = {
    "in_domain": "in_domain",
    "qualified": "qualified",
    "abstain_outcome": "abstained",
    "out_of_domain": "out_of_domain",
}

REQUIRED_INDICATORS = ("gdd", "precipitation_total", "frost_window", "om_r_0_30cm")

STANDING_LIMITATIONS = (
    ("Marsden Farm is one research site over nine seasons. Nothing here predicts what will happen on this "
    "field."),
    "Climate indicators are POWER grid values, about 50 km across, not field measurements.",
    "Soil values come from a mapped survey, not from sampling this field.",
    "Every applicability rule is a team-proposed guardrail and is not expert-reviewed.",
    "No profitability is calculated; the data PRD 9 requires for it is not available.",
)


CONSTRAINT_KEYS = (
    "manure_access",
    "forage_use_or_buyer",
    "oat_use_or_buyer",
    "small_grain_equipment_or_contractor",
)


def _normalise_nulls(instance: object, names: tuple[str, ...]) -> None:
    """Turn JSON null into UNKNOWN on a frozen dataclass.

    The frontend sends null for "not answered" and "Not sure". Left as None it would be a known value
    to every operator, so no is_unknown rule would fire and an unanswered question would read as
    available. Normalising at the boundary makes that impossible rather than merely documented.
    """
    for name in names:
        if getattr(instance, name) is None:
            object.__setattr__(instance, name, UNKNOWN)


@dataclass(frozen=True)
class FieldProfile:
    """What the profile endpoints know about a field, reduced to what the rules read."""

    field_id: str
    boundary_source: str
    crop_history_summary: str
    county: str | _Unknown = UNKNOWN
    crop_history_is_maize_soybean: bool | _Unknown = UNKNOWN
    gdd_season_difference_vs_marsden: float | _Unknown = UNKNOWN
    frost_free_days: int | _Unknown = UNKNOWN
    dominant_drainage_class: str | _Unknown = UNKNOWN
    indicator_statuses: Mapping[str, str] = dataclass_field(default_factory=dict)

    def __post_init__(self) -> None:
        _normalise_nulls(
            self,
            (
                "county",
                "crop_history_is_maize_soybean",
                "gdd_season_difference_vs_marsden",
                "frost_free_days",
                "dominant_drainage_class",
            ),
        )

    def unknown_required_indicators(self) -> tuple[str, ...]:
        return tuple(
            indicator
            for indicator in REQUIRED_INDICATORS
            if self.indicator_statuses.get(indicator, "unknown") != "ok"
        )


@dataclass(frozen=True)
class FarmerConstraints:
    """What the farmer has told us. Anything unstated stays UNKNOWN, never False."""

    manure_access: bool | _Unknown = UNKNOWN
    forage_use_or_buyer: bool | _Unknown = UNKNOWN
    oat_use_or_buyer: bool | _Unknown = UNKNOWN
    small_grain_equipment_or_contractor: bool | _Unknown = UNKNOWN
    priorities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _normalise_nulls(self, CONSTRAINT_KEYS)

    @classmethod
    def from_mapping(cls, answers: Mapping[str, object]) -> FarmerConstraints:
        """Build from the frontend's engine context, where JSON null means unknown.

        The priorities screen emits ``boolean | null`` per key (see
        ``web/src/features/priorities/engine-context.ts``). Passing that through unconverted would make
        every unstated answer look like a known value, which is the one failure this engine exists to
        prevent, so the conversion lives here rather than in each caller.
        """
        return cls(
            **{key: answers.get(key, UNKNOWN) for key in CONSTRAINT_KEYS},
            priorities=tuple(answers.get("priorities", ()) or ()),
        )


@dataclass(frozen=True)
class RuleFinding:
    rule_id: str
    target: str
    effect: str
    condition_text: str
    rationale: str
    review: str


@dataclass(frozen=True)
class OutcomeAssessment:
    outcome_id: str
    label: str
    status: str
    claimable: bool
    evidence_type: str | None
    source: str | None
    statement: str | None
    caution: str
    findings: tuple[RuleFinding, ...] = ()


@dataclass(frozen=True)
class StrategyAssessment:
    strategy_id: str
    label: str
    rotation: str
    feasibility: str
    operational_requirements: tuple[str, ...]
    findings: tuple[RuleFinding, ...] = ()


@dataclass(frozen=True)
class Decision:
    field_id: str
    boundary_source: str
    crop_history_summary: str
    outcome: str
    outcome_reason: str
    strategies: tuple[StrategyAssessment, ...]
    outcomes: tuple[OutcomeAssessment, ...]
    unknowns: tuple[str, ...]
    constraints_recorded: Mapping[str, object]
    priorities_recorded: tuple[str, ...]
    rules_version: str
    limitations: tuple[str, ...]

    def candidate_strategies(self) -> tuple[str, ...]:
        return tuple(
            assessment.strategy_id
            for assessment in self.strategies
            if assessment.strategy_id != "A" and assessment.feasibility != "unavailable"
        )


def build_context(profile: FieldProfile, constraints: FarmerConstraints) -> dict[str, object]:
    """Flatten the profile and constraints onto the context keys the rule table reads."""
    return {
        "county": profile.county,
        "crop_history_is_maize_soybean": profile.crop_history_is_maize_soybean,
        "gdd_season_difference_vs_marsden": profile.gdd_season_difference_vs_marsden,
        "frost_free_days": profile.frost_free_days,
        "dominant_drainage_class": profile.dominant_drainage_class,
        "manure_access": constraints.manure_access,
        "forage_use_or_buyer": constraints.forage_use_or_buyer,
        "oat_use_or_buyer": constraints.oat_use_or_buyer,
        "small_grain_equipment_or_contractor": constraints.small_grain_equipment_or_contractor,
        "required_indicators_all_known": not profile.unknown_required_indicators(),
    }


def rule_applies(rule: rules.ApplicabilityRule, context: Mapping[str, object]) -> bool:
    """Whether one rule's condition holds. An unknown value fires only the is_unknown operator."""
    value = context.get(rule.context_key, UNKNOWN)
    if rule.operator == "is_unknown":
        return value is UNKNOWN
    if value is UNKNOWN:
        return False

    if rule.operator == "equals":
        return value == rule.value
    if rule.operator == "not_equals":
        return value != rule.value
    if rule.operator == "in":
        return value in rule.value
    if rule.operator == "not_in":
        return value not in rule.value
    if rule.operator in ("lt", "lte", "gt", "gte"):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(
                f"rule {rule.rule_id} compares {rule.context_key} numerically, got {value!r}"
            )
        if rule.operator == "lt":
            return value < rule.value
        if rule.operator == "lte":
            return value <= rule.value
        if rule.operator == "gt":
            return value > rule.value
        return value >= rule.value
    raise ValueError(f"rule {rule.rule_id} uses an unsupported operator: {rule.operator}")


def _finding(rule: rules.ApplicabilityRule) -> RuleFinding:
    return RuleFinding(
        rule_id=rule.rule_id,
        target=rule.outcome_id,
        effect=rule.effect,
        condition_text=rule.condition_text,
        rationale=rule.rationale,
        review=rule.review,
    )


def fired_rules(context: Mapping[str, object]) -> tuple[RuleFinding, ...]:
    """Every rule whose condition holds, in table order."""
    return tuple(_finding(rule) for rule in rules.APPLICABILITY_RULES if rule_applies(rule, context))


def _worst(effects: Sequence[str]) -> str:
    return max(effects, key=SEVERITY.index) if effects else "in_domain"


def _assess_outcome(
    outcome: rules.OutcomeEvidence,
    findings: Sequence[RuleFinding],
) -> OutcomeAssessment:
    if not outcome.claimable:
        return OutcomeAssessment(
            outcome_id=outcome.outcome_id,
            label=outcome.label,
            status="not_assessed",
            claimable=False,
            evidence_type=None,
            source=None,
            statement=None,
            caution=outcome.what_may_not_be_said,
        )

    relevant = [
        finding
        for finding in findings
        if finding.target in (outcome.outcome_id, rules.WHOLE_COMPARISON_TARGET)
    ]
    status = OUTCOME_STATUS_FROM_EFFECT[_worst([finding.effect for finding in relevant])]
    speakable = status in ("in_domain", "qualified")
    return OutcomeAssessment(
        outcome_id=outcome.outcome_id,
        label=outcome.label,
        status=status,
        claimable=True,
        evidence_type=outcome.evidence_type,
        source=outcome.source,
        statement=outcome.what_may_be_said if speakable else None,
        caution=outcome.what_may_not_be_said,
        findings=tuple(relevant),
    )


FEASIBILITY_TARGET = {"B": "strategy_b_feasibility", "C": "strategy_c_feasibility"}
FEASIBILITY_FROM_EFFECT = {
    "in_domain": "available",
    "qualified": "qualified",
    "abstain_outcome": "qualified",
    "out_of_domain": "unavailable",
}


def _assess_strategy(
    profile_findings: Sequence[RuleFinding],
    strategy: rules.StrategyProfile,
) -> StrategyAssessment:
    target = FEASIBILITY_TARGET.get(strategy.strategy_id)
    relevant = [finding for finding in profile_findings if finding.target == target] if target else []
    comparison_blocked = any(
        finding.target == rules.WHOLE_COMPARISON_TARGET and finding.effect == "out_of_domain"
        for finding in profile_findings
    )
    effect = _worst([finding.effect for finding in relevant])
    feasibility = "unavailable" if comparison_blocked else FEASIBILITY_FROM_EFFECT[effect]
    return StrategyAssessment(
        strategy_id=strategy.strategy_id,
        label=strategy.label,
        rotation=strategy.rotation,
        feasibility=feasibility,
        operational_requirements=strategy.operational_requirements,
        findings=tuple(relevant),
    )


def _collect_unknowns(
    profile: FieldProfile,
    constraints: FarmerConstraints,
    context: Mapping[str, object],
) -> tuple[str, ...]:
    unknown_keys = sorted(key for key, value in context.items() if value is UNKNOWN)
    missing_indicators = [
        f"indicator {indicator}" for indicator in profile.unknown_required_indicators()
    ]
    return tuple(unknown_keys + missing_indicators)


def _decide(
    outcomes: Sequence[OutcomeAssessment],
    strategies: Sequence[StrategyAssessment],
    findings: Sequence[RuleFinding],
) -> tuple[str, str]:
    blocking = [
        finding
        for finding in findings
        if finding.target == rules.WHOLE_COMPARISON_TARGET and finding.effect == "out_of_domain"
    ]
    if blocking:
        reasons = ", ".join(finding.rule_id for finding in blocking)
        return "abstention", f"the field is outside the supported domain ({reasons})"

    claimable = [outcome for outcome in outcomes if outcome.claimable]
    speakable = [outcome for outcome in claimable if outcome.status in ("in_domain", "qualified")]
    if not speakable:
        return (
            "abstention",
            "no claimable outcome survived the applicability rules, so there is nothing to compare",
        )

    candidates = [
        strategy
        for strategy in strategies
        if strategy.strategy_id != "A" and strategy.feasibility == "available"
    ]
    unqualified = [outcome for outcome in claimable if outcome.status == "in_domain"]

    if candidates and len(unqualified) == len(claimable):
        names = ", ".join(strategy.strategy_id for strategy in candidates)
        return (
            "strategy_worth_exploring",
            (
                f"strategy {names} is operationally available and every claimable outcome is in domain; "
                "this is a candidate for local evaluation, not a recommendation"
            ),
        )

    withheld = [outcome for outcome in claimable if outcome.status not in ("in_domain", "qualified")]
    detail = (
        f"{len(withheld)} of {len(claimable)} claimable outcomes were withheld"
        if withheld
        else "some dimensions are qualified"
    )
    return (
        "qualified_comparison",
        f"the strategies can be compared but not separated: {detail}",
    )


def assess(profile: FieldProfile, constraints: FarmerConstraints) -> Decision:
    """Compare the three strategies for one field. Returns one of the three PRD 8.3 outcomes."""
    context = build_context(profile, constraints)
    findings = fired_rules(context)

    outcomes = tuple(_assess_outcome(outcome, findings) for outcome in rules.OUTCOME_EVIDENCE)
    strategies = tuple(_assess_strategy(findings, strategy) for strategy in rules.STRATEGY_PROFILES)
    outcome, reason = _decide(outcomes, strategies, findings)

    return Decision(
        field_id=profile.field_id,
        boundary_source=profile.boundary_source,
        crop_history_summary=profile.crop_history_summary,
        outcome=outcome,
        outcome_reason=reason,
        strategies=strategies,
        outcomes=outcomes,
        unknowns=_collect_unknowns(profile, constraints, context),
        constraints_recorded={
            "manure_access": constraints.manure_access,
            "forage_use_or_buyer": constraints.forage_use_or_buyer,
            "oat_use_or_buyer": constraints.oat_use_or_buyer,
            "small_grain_equipment_or_contractor": constraints.small_grain_equipment_or_contractor,
        },
        priorities_recorded=constraints.priorities,
        rules_version=rules.RULES_VERSION,
        limitations=STANDING_LIMITATIONS,
    )
