"""The field profile screen's data, from stored facts. Real values only: never sample data.

Shape: `FieldProfile` in `web/src/features/profile/types.ts`. A section whose data does not exist is
`not_loaded` with `data: null`, never an empty list or a zero.
"""
from __future__ import annotations

import calendar

from api.core.crop_summary import describe_sequence
from api.core.lineage import lineage_for, thresholds
from api.db.facts import (
    FIRST_CROP_YEAR,
    MAJORITY_PCT,
    FieldRecord,
    IndicatorFacts,
    SeasonalMean,
    SoilMeasure,
)
from api.schemas import (
    ClimateOut,
    CropHistoryOut,
    CropYearOut,
    FieldProfileOut,
    IndicatorOut,
    ProfileVersionsOut,
    ProvenanceOut,
    SectionOut,
    SoilMeasureOut,
    SoilOut,
    TechnicalOut,
)
from engine.rules import strategy_rules as rules

NOT_LOADED = {"status": "not_loaded", "data": None, "provenance": None}

CROP_PROVENANCE = ProvenanceOut(
    title="What was grown each year",
    what_it_is=(
        "For each year, the crop that USDA's satellite-based crop map assigned to this field's squares."
    ),
    source="USDA NASS Cropland Data Layer",
    source_url="https://www.nass.usda.gov/Research_and_Science/Cropland/",
    precision=(
        "30 m squares. It is USDA's best estimate from satellites, not a record kept by the farm, so "
        "agreeing with it is not independent proof. The map is sharper from 2024 (10 m), but 2024 and "
        "2025 here use the 30 m version."
    ),
    gaps="Years before 2015 are not loaded.",
    technical=TechnicalOut(
        evidence_type="classified",
        scale="30 m cells inside the field",
        product="USDA NASS CDL 2015 to 2025",
        indicator_id="cdl.crop_history.2015_2025",
    ),
)

YOUR_INPUT_PROVENANCE = ProvenanceOut(
    title="What you told us you grew",
    what_it_is="The crop you named for each season from 2015 to 2025.",
    source="Your own answers",
    source_url=None,
    precision=(
        "From your memory or records. AgroCycle has not checked it against any map or data, so it is shown as "
        "your input, not as a finding."
    ),
    gaps="Weather and soil have not been prepared for a boundary you draw, so they show as not loaded.",
    technical=TechnicalOut(
        evidence_type="assumption",
        scale="your whole field",
        product="Your answers",
        indicator_id="farmer.crop_history.2015_2025",
    ),
)


def _soil_provenance(has_measures: bool) -> ProvenanceOut:
    if not has_measures:
        return ProvenanceOut(
            title="The soil",
            what_it_is="The soil type that USDA's soil survey maps at the centre of this field.",
            source="USDA NRCS Soil Survey (SSURGO)",
            source_url="https://websoilsurvey.nrcs.usda.gov/app/",
            precision=(
                "A mapped soil unit, not a soil test from this field. Only the point at the field's "
                "centre is read, not an average over the whole field."
            ),
            gaps="Drainage, organic matter and texture are not loaded yet.",
            technical=TechnicalOut(
                evidence_type="survey",
                scale="Mapped soil unit at the field centre point",
                product="SSURGO map unit",
                indicator_id="ssurgo.map_unit.field_centre",
            ),
        )
    return ProvenanceOut(
        title="The soil",
        what_it_is=(
            "The soil type that USDA's soil survey maps at the centre of this field, and survey values "
            "averaged over the soil units mapped inside the field."
        ),
        source="USDA NRCS Soil Survey (SSURGO)",
        source_url="https://websoilsurvey.nrcs.usda.gov/app/",
        precision=(
            "Soil type and map unit are read at the field's centre. The measures are averages over the "
            "mapped soil units inside the field, weighted by area and by how much of each unit each soil "
            "makes up, for the top 30 cm (water storage: the top 100 cm). They are survey estimates, not "
            "soil tests from this field. The survey does not record drainage tiles."
        ),
        gaps=(
            "Where a soil unit has no value, the average is marked partial and says how much of the "
            "field it covers. Values that could not be computed are not shown."
        ),
        technical=TechnicalOut(
            evidence_type="survey",
            scale="Mapped soil units: type at the field centre, measures weighted over the field",
            product="SSURGO map units, components and horizons",
            indicator_id="ssurgo.map_unit.field_centre; ssurgo.area_weighted_measures",
        ),
    )


def _crop_history(record: FieldRecord) -> SectionOut[CropHistoryOut]:
    if not record.crop_sequence:
        return SectionOut[CropHistoryOut](**NOT_LOADED)
    summary = describe_sequence(record.crop_sequence, FIRST_CROP_YEAR)
    years = [
        CropYearOut(year=FIRST_CROP_YEAR + index, code=code)
        for index, code in enumerate(record.crop_sequence)
    ]
    repeated = [
        entry.year for index, entry in enumerate(years) if index and entry.code == years[index - 1].code
    ]
    return SectionOut[CropHistoryOut](
        status="available",
        data=CropHistoryOut(years=years, summary=summary, repeated_years=repeated),
        provenance=YOUR_INPUT_PROVENANCE if record.boundary_source == "drawn" else CROP_PROVENANCE,
    )


def _partial(measure: SoilMeasure | None) -> str:
    return f" Partial: {measure.coverage_note}." if measure and measure.coverage_note else ""


def _soil_measures(facts: IndicatorFacts) -> list[SoilMeasureOut]:
    """Survey values with a plain note each. Only what the data holds; nothing is filled in."""
    soil = facts.soil
    out: list[SoilMeasureOut] = []

    om = soil.get("om_r_0_30cm")
    if om:
        out.append(
            SoilMeasureOut(
                label="Organic matter, top 30 cm",
                value=f"{om.value:.1f} %",
                note="Survey estimate, averaged over the field." + _partial(om),
            )
        )

    parts = [soil.get(i) for i in ("claytotal_r_0_30cm", "silttotal_r_0_30cm", "sandtotal_r_0_30cm")]
    if all(parts):
        clay, silt, sand = parts  # type: ignore[misc]
        out.append(
            SoilMeasureOut(
                label="Texture, top 30 cm",
                value=f"clay {clay.value:.0f} %, silt {silt.value:.0f} %, sand {sand.value:.0f} %",
                note=(
                    "Each part is averaged on its own, so together they may not add up to exactly "
                    "100 %." + "".join(_partial(p) for p in parts)
                ),
            )
        )

    ph = soil.get("ph1to1h2o_r_0_30cm")
    if ph:
        out.append(
            SoilMeasureOut(
                label="Acidity, top 30 cm",
                value=f"pH {ph.value:.1f}",
                note="Survey estimate." + _partial(ph),
            )
        )

    water = soil.get("available_water_storage_0_100cm")
    if water:
        out.append(
            SoilMeasureOut(
                label="Water the soil can store for plants, top 100 cm",
                value=f"{water.value:.1f} cm",
                note="Survey estimate of what the soil can hold, not how wet it is." + _partial(water),
            )
        )

    if facts.drainage_shares:
        shown = facts.drainage_shares[:3]
        rest = sum(share for _, share in facts.drainage_shares[3:])
        text = ", ".join(f"{label.lower() if i else label} {share:.0f} %" for i, (label, share) in enumerate(shown))
        if rest >= 1:
            text += f", other {rest:.0f} %"
        total = sum(share for _, share in facts.drainage_shares)
        mixed = total > 0 and facts.drainage_shares[0][1] / total * 100 <= MAJORITY_PCT
        out.append(
            SoilMeasureOut(
                label="Drainage",
                value=text,
                note=(
                    "Share of the field's mapped area. No single class covers more than half, so the field is "
                    "mixed and we show the shares instead of naming one class. "
                    if mixed
                    else "Share of the field's mapped area. "
                )
                + "The survey does not record drainage tiles.",
            )
        )
    return out


def _soil(record: FieldRecord, facts: IndicatorFacts) -> SectionOut[SoilOut]:
    measures = _soil_measures(facts)
    has_point_reading = bool(record.soil_series and record.soil_map_unit)
    if not has_point_reading and not measures:
        return SectionOut[SoilOut](**NOT_LOADED)
    has_texture = all(
        i in facts.soil for i in ("claytotal_r_0_30cm", "silttotal_r_0_30cm", "sandtotal_r_0_30cm")
    )
    missing = [
        label
        for label, present in (
            ("How well it drains", bool(facts.drainage_shares)),
            ("Organic matter", "om_r_0_30cm" in facts.soil),
            ("Soil texture", has_texture),
        )
        if not present
    ]
    return SectionOut[SoilOut](
        status="available",
        data=SoilOut(
            # A boundary a farmer drew has no soil type read at a centre point, only measures averaged over the
            # soil units mapped inside it. Say that, instead of hiding real measures or naming a type nobody read.
            series=record.soil_series or "Several soil types",
            map_unit=record.soil_map_unit or "No single soil type is named: the measures below are averaged over the units mapped inside your boundary.",
            sampling_note=(
                "Soil type is read at the centre point of the field. The measures below are "
                "averaged over the soil units mapped inside it."
                if has_point_reading and measures
                else "The measures below are averaged by area over the soil units mapped inside your boundary."
                if measures
                else "Read at the centre point of the field, not averaged over its area."
            ),
            measures=measures,
            not_loaded=missing,
        ),
        provenance=_soil_provenance(bool(measures)),
    )


def _month(number: int) -> str:
    return calendar.month_name[number]


def _indicator_card(mean: SeasonalMean) -> IndicatorOut:
    """One weather card. Plain wording is here; source, scale, limits and thresholds come from DS2."""
    lineage = lineage_for(mean.indicator_id)
    t = thresholds()
    window = f"{_month(mean.start_month)} to {_month(mean.end_month)}"
    based_on = f"Based on {mean.seasons_used} of {mean.seasons_total} seasons."

    if mean.indicator_id == "precipitation_total":
        card_id, title = "gs-rain", "Rain while crops grow"
        label = f"Rain from {window}"
        value = f"{round(mean.mean)} mm"
        context = f"About {round(mean.mean / 25.4)} inches, added up for each season and then averaged. {based_on}"
        what = (
            f"All the rain from {window}, added up for each season, then averaged over the seasons."
        )
    elif mean.indicator_id == "heat_days":
        heat = f"{t['heat_day_c']:g}"
        card_id, title = "hot-days", "Very hot days"
        label = f"Very hot days ({heat} °C or more)"
        value = f"{round(mean.mean)} a season"
        context = f"Days when the highest air temperature reached {heat} °C. {based_on}"
        what = (
            f"The number of days from {window} when the highest air temperature was {heat} °C or "
            "more, averaged over the seasons."
        )
    elif mean.indicator_id == "dry_spell_count":
        days = f"{t['dry_spell_min_days']:g}"
        card_id, title = "dry-spells", "Dry spells"
        label = f"Dry spells of {days} or more days with no rain"
        value = f"{mean.mean:.1f} a season"
        context = f"Runs of {days} days or more with under {t['wet_day_mm']:g} mm of rain a day. {based_on}"
        what = (
            f"Runs of {days} or more days in a row with under {t['wet_day_mm']:g} mm of rain a day, "
            f"counted from {window} and averaged over the seasons."
        )
    else:  # gdd
        card_id, title = "gdd", "Warmth for crop growth"
        label = "Warmth for crop growth"
        value = f"{round(mean.mean):,}"
        context = (
            f"Growing degree days, {window} (base {t['gdd_base_c']:g} °C, capped at "
            f"{t['gdd_cap_c']:g} °C). {based_on}"
        )
        what = (
            "Growing degree days add up how much warmth crops got each day "
            f"(above {t['gdd_base_c']:g} °C, capped at {t['gdd_cap_c']:g} °C), from {window}, "
            "averaged over the seasons."
        )

    left_out = mean.seasons_total - mean.seasons_used
    gaps = lineage["missing_data_rule"]
    if left_out:
        gaps += f" {left_out} of {mean.seasons_total} seasons were left out of the average."

    return IndicatorOut(
        id=card_id,
        label=label,
        value=value,
        context=context,
        provenance=ProvenanceOut(
            title=title,
            what_it_is=what,
            source=lineage["source"],
            source_url=lineage["source_url"],
            precision=f"{lineage['spatial_scale']} {lineage['limitation']}",
            gaps=gaps,
            technical=TechnicalOut(
                evidence_type=lineage["evidence_type"],
                scale=lineage["spatial_scale"].split(". ")[0],
                indicator_id=lineage["indicator_id"],
                variable=", ".join(lineage["variables"]),
            ),
        ),
    )


def _climate(facts: IndicatorFacts) -> SectionOut[ClimateOut]:
    if not facts.seasonal:
        return SectionOut[ClimateOut](**NOT_LOADED)
    ordered = [facts.seasonal[i] for i in ("precipitation_total", "heat_days", "dry_spell_count", "gdd") if i in facts.seasonal]
    first, last = min(m.first_year for m in ordered), max(m.last_year for m in ordered)
    return SectionOut[ClimateOut](
        status="available",
        data=ClimateOut(
            period_label=f"Averages over the seasons {first} to {last}",
            indicators=[_indicator_card(m) for m in ordered],
        ),
        provenance=None,
    )


def build_profile_view(
    record: FieldRecord, facts: IndicatorFacts, data_version: str = "unknown"
) -> FieldProfileOut:
    return FieldProfileOut(
        field_id=record.field_id,
        versions=ProfileVersionsOut(
            data_version=data_version,
            engine_version=rules.RULES_VERSION,
            crop_history_period=f"{FIRST_CROP_YEAR}-{FIRST_CROP_YEAR + len(record.crop_sequence or '') - 1}"
            if record.crop_sequence
            else "not loaded",
            crop_history_source=(
                "Your own answers" if record.boundary_source == "drawn" else "USDA NASS Cropland Data Layer (30 m)"
            ),
        ),
        crop_history=_crop_history(record),
        climate=_climate(facts),
        # No HLS greenness features exist yet (roadmap Phase 5), so there is nothing to show.
        vegetation=SectionOut[None](**NOT_LOADED),
        soil=_soil(record, facts),
    )
