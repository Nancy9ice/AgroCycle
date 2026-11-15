"""F1 — Ask AgroCycle: grounded AI assistant.

Answers questions about one field's profile or one stored comparison. The model
only sees the stored analysis/profile + lineage rows — no external knowledge, no
live retrieval. Every Q&A is logged for the Phase 15 claim check.

Guardrails enforced here:
- Context is built entirely from stored data: analysis JSON, field record, lineage rows.
- Claude is forced to call the `provide_answer` tool (structured output via tool_choice).
- Citations are validated: any indicator_id not in the context is stripped.
- Forbidden words from spec §7 are scrubbed from the answer before returning.
- If ANTHROPIC_API_KEY is absent the endpoint returns 503; nothing fails at import.
"""
from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from api.db.facts import FieldRecord, IndicatorFacts

MODEL = "claude-opus-4-7"

# Spec §7 — words the response must never contain.
_FORBIDDEN = [
    "recommended",
    "recommendation",
    "best rotation",
    "best option",
    "best choice",
    "will improve",
    "guaranteed",
    "measured soil health",
    "yield prediction",
    "yield will",
]

_SYSTEM_BASE = """\
You are AgroCycle's assistant. AgroCycle is a crop-rotation decision-support tool for Iowa farmers.
You answer questions strictly from the CONTEXT section below — the field's environmental data, its
comparison result and the indicator lineage records. You do not use outside knowledge.

HARD RULES
1. Only use facts from the CONTEXT section. Do not draw on outside agronomic knowledge.
2. When you cite a number or finding, name its indicator ID from the AVAILABLE INDICATORS list using
   the exact ID string.
3. If a question asks about yield forecasts, profit figures, specific costs, advice about other
   regions, other farms, or anything not covered by the context, set refused = true and explain
   the gap in one sentence.
4. Never use these words: "recommended", "best", "will improve", "guaranteed",
   "measured soil health", "yield prediction".
5. Never rank strategies A, B, C or declare a winner.
6. Keep answers short: 2–4 sentences for farmer mode, up to 6 for adviser mode.
"""

_FARMER_STYLE = """\
AUDIENCE: farmer — use plain words. Replace technical terms:
  "abstention"              → "not enough to say"
  "qualified comparison"    → "no clear winner yet"
  "worth exploring"         → "worth a closer look"
  "NDVI / HLS"              → "how green the field looks from satellite"
  "CDL"                     → "USDA's crop map"
  "SSURGO"                  → "USDA's soil survey"
  "NASA POWER / reanalysis" → "NASA weather data for a ~50 km area"
  "not assessed"            → "not checked yet"
Avoid jargon. Short sentences. Plain English only.\
"""

_ADVISER_STYLE = """\
AUDIENCE: adviser — you may use technical terms (evidence types, indicator IDs, scale qualifiers,
CDL, SSURGO, GDD, reanalysis, etc.). Explain the engine's reasoning clearly and cite indicator IDs
when you reference a number.\
"""

_TOOL = {
    "name": "provide_answer",
    "description": "Return your answer to the question about this field's crop-rotation data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "refused": {
                "type": "boolean",
                "description": (
                    "true when the question is outside the available context (yield, profit,"
                    " other regions, other farms, or anything not in the CONTEXT section)."
                ),
            },
            "answer": {
                "type": "string",
                "description": (
                    "Your answer. Must not be empty even when refused=true"
                    " — explain what is and is not available in one sentence."
                ),
            },
            "citations": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Indicator IDs from AVAILABLE INDICATORS that you cited. "
                    "Use the exact ID strings. Empty array if none were cited."
                ),
            },
        },
        "required": ["refused", "answer", "citations"],
    },
}


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def build_analysis_context(analysis: dict, lineage_rows: list[dict]) -> tuple[str, list[str]]:
    """Return (context_text, indicator_ids_in_context) for a stored compare result."""
    decision = analysis.get("decision", {})
    field = analysis.get("field", {})

    parts = [
        "=== FIELD ===",
        f"ID: {field.get('field_id', 'unknown')}",
        f"County: {field.get('county', 'unknown')}",
        f"Crop history class: {field.get('field_class') or 'not classified'}",
        "",
        "=== COMPARISON RESULT ===",
        f"Outcome: {decision.get('outcome', 'unknown')}",
        f"Reason: {decision.get('outcome_reason', '')}",
        f"Crop history summary: {decision.get('crop_history_summary', '')}",
        "",
    ]

    unknowns = decision.get("unknowns", [])
    if unknowns:
        parts.append("What was not known (farmer did not answer):")
        for u in unknowns:
            parts.append(f"  - {u}")
        parts.append("")

    cr = decision.get("constraints_recorded", {})
    parts += [
        "=== FARMER ANSWERS ===",
        f"Manure access: {cr.get('manure_access')}",
        f"Forage use or buyer: {cr.get('forage_use_or_buyer')}",
        f"Oat use or buyer: {cr.get('oat_use_or_buyer')}",
        f"Small grain equipment/contractor: {cr.get('small_grain_equipment_or_contractor')}",
        f"Priorities: {', '.join(decision.get('priorities_recorded', [])) or 'none stated'}",
        "",
    ]

    for strat in decision.get("strategies", []):
        parts.append(
            f"=== STRATEGY {strat['strategy_id']} — {strat['label']} ({strat['rotation']}) ==="
        )
        parts.append(f"Feasibility: {strat['feasibility']}")
        for op in strat.get("operational_requirements", []):
            parts.append(f"  Requires: {op}")
        for f_item in strat.get("findings", []):
            parts.append(
                f"  Rule {f_item['rule_id']}: {f_item['condition_text']} → {f_item['effect']}"
            )
        parts.append("")

    for outcome in decision.get("outcomes", []):
        parts.append(f"=== OUTCOME: {outcome['label']} ===")
        parts.append(f"Status: {outcome['status']}, Claimable: {outcome['claimable']}")
        if outcome.get("statement"):
            parts.append(f"Statement: {outcome['statement']}")
        if outcome.get("caution"):
            parts.append(f"Caution: {outcome['caution']}")
        parts.append("")

    parts += [
        "=== WHAT THIS DATA CANNOT SAY ===",
        "- All climate indicators are grid-scale (~50 km), not field-scale measurements.",
        "- Soil data is from the USDA survey, not a soil test from this specific field.",
        "- The Marsden Farm trial is one research farm in Iowa, 2003–2011. Not a prediction.",
        "- Crop history is USDA's satellite estimate, not farm records.",
        "- The engine never ranks strategies or picks a winner.",
        "",
    ]

    indicator_ids: list[str] = []
    if lineage_rows:
        parts.append("=== AVAILABLE INDICATORS ===")
        for lin in lineage_rows:
            ind_id = lin.get("indicator_id", "")
            indicator_ids.append(ind_id)
            parts.append(
                f"{ind_id}: {lin.get('label', '')} | "
                f"scale: {lin.get('scale', '')} | "
                f"limitation: {lin.get('limitation', '')}"
            )
        parts.append("")

    return "\n".join(parts), indicator_ids


def build_profile_context(
    record: FieldRecord,
    facts: IndicatorFacts,
    lineage_rows: list[dict],
) -> tuple[str, list[str]]:
    """Return (context_text, indicator_ids_in_context) for a field profile."""
    parts = [
        "=== FIELD ===",
        f"ID: {record.field_id}",
        f"County: {record.county}",
        f"Boundary: {record.boundary_source} (demonstration polygon, not a real farm boundary)",
        f"Crop history class: {record.field_class or 'not classified'}",
        f"Crop sequence 2015–2025: {record.crop_sequence or 'not loaded'}",
        "",
    ]

    if record.soil_series or record.soil_map_unit:
        parts += [
            "=== SOIL ===",
            f"Series: {record.soil_series or 'unknown'}",
            f"Map unit: {record.soil_map_unit or 'unknown'}",
        ]
        if facts.dominant_drainage_class:
            parts.append(f"Dominant drainage: {facts.dominant_drainage_class}")
        if facts.drainage_shares:
            shares = ", ".join(
                f"{lbl} {share:.0f}%" for lbl, share in facts.drainage_shares[:3]
            )
            parts.append(f"Drainage mix: {shares}")
        parts.append("")

    if facts.seasonal:
        parts.append("=== CLIMATE INDICATORS (seasonal means) ===")
        for ind_id, mean in facts.seasonal.items():
            parts.append(
                f"{ind_id}: mean {mean.mean:.1f} {mean.unit}, "
                f"{mean.seasons_used}/{mean.seasons_total} seasons, "
                f"{mean.first_year}–{mean.last_year}"
            )
        parts.append("")

    if facts.gdd_season_difference_vs_marsden is not None:
        parts.append(
            f"GDD distance vs Marsden Farm: {facts.gdd_season_difference_vs_marsden:.0f} °C·days"
        )
    if facts.frost_free_days is not None:
        parts.append(f"Frost-free days (mean): {facts.frost_free_days}")
    if facts.gdd_season_difference_vs_marsden is not None or facts.frost_free_days is not None:
        parts.append("")

    parts += [
        "=== WHAT THIS DATA CANNOT SAY ===",
        "- All climate indicators are grid-scale (~50 km), not field-scale measurements.",
        "- Soil data is from the USDA survey, not a soil test from this specific field.",
        "- Crop history is USDA's satellite estimate, not farm records.",
        "",
    ]

    indicator_ids: list[str] = []
    if lineage_rows:
        parts.append("=== AVAILABLE INDICATORS ===")
        for lin in lineage_rows:
            ind_id = lin.get("indicator_id", "")
            indicator_ids.append(ind_id)
            parts.append(
                f"{ind_id}: {lin.get('label', '')} | "
                f"scale: {lin.get('scale', '')} | "
                f"limitation: {lin.get('limitation', '')}"
            )
        parts.append("")

    return "\n".join(parts), indicator_ids


# ---------------------------------------------------------------------------
# Claude call
# ---------------------------------------------------------------------------

def call_claude(
    context: str,
    indicator_ids: list[str],
    question: str,
    audience: Literal["farmer", "adviser"],
) -> dict[str, Any]:
    """Call claude-opus-4-7 with grounded context and return structured answer.

    Uses:
    - tool_choice forced to `provide_answer` for guaranteed structured output
    - cache_control on system + context blocks so follow-up questions are fast
    - Citation validation: strips any ID not present in the context
    - Forbidden-word scrub on the answer (spec §7)
    """
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "refused": True,
            "answer": "The AI assistant is not configured. Add ANTHROPIC_API_KEY to the server environment.",
            "citations": [],
            "model": MODEL,
        }

    client = anthropic.Anthropic(api_key=api_key, timeout=45.0)
    style = _FARMER_STYLE if audience == "farmer" else _ADVISER_STYLE

    ind_list = (
        "\n".join(f"  {i}" for i in indicator_ids)
        if indicator_ids
        else "  (none — this context has no indicator records)"
    )

    system_text = (
        f"{_SYSTEM_BASE}\n{style}\n\n"
        f"AVAILABLE INDICATOR IDs (use exact strings for citations):\n{ind_list}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"CONTEXT:\n{context}",
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": f"QUESTION: {question}",
                    },
                ],
            }
        ],
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "provide_answer"},
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "provide_answer":
            raw = block.input
            valid_ids = set(indicator_ids)
            citations = [c for c in raw.get("citations", []) if c in valid_ids]
            answer = _scrub(raw.get("answer", ""))
            return {
                "refused": bool(raw.get("refused", False)),
                "answer": answer,
                "citations": citations,
                "model": MODEL,
            }

    return {
        "refused": True,
        "answer": "Could not generate an answer. Please try rephrasing your question.",
        "citations": [],
        "model": MODEL,
    }


def _scrub(text: str) -> str:
    """Remove spec §7 forbidden words from the answer."""
    for word in _FORBIDDEN:
        text = re.sub(
            rf"\b{re.escape(word)}\b",
            "worth considering",
            text,
            flags=re.IGNORECASE,
        )
    return text
