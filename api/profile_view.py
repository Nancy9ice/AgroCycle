"""The field profile screen's data, from stored facts. Real values only: never sample data.

Shape: `FieldProfile` in `web/src/features/profile/types.ts`. A section whose data does not exist is
`not_loaded` with `data: null`, never an empty list or a zero.
"""
from __future__ import annotations

import calendar

from .crop_summary import describe_sequence
from .facts import FIRST_CROP_YEAR, FieldRecord, IndicatorFacts, SeasonalMean
from .lineage import lineage_for, thresholds
from .schemas import (
    ClimateOut,
    CropHistoryOut,
    CropYearOut,
    FieldProfileOut,
    IndicatorOut,
    ProvenanceOut,
    SectionOut,
    SoilOut,
    TechnicalOut,
)

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

SOIL_PROVENANCE = ProvenanceOut(
    title="The soil",
    what_it_is="The soil type that USDA's soil survey maps at the centre of this field.",
    source="USDA NRCS Soil Survey (SSURGO)",
    source_url="https://websoilsurvey.nrcs.usda.gov/app/",
    precision=(
        "A mapped soil unit, not a soil test from this field. Only the point at the field's centre is "
        "read, not an average over the whole field."
    ),
    gaps="Drainage, organic matter and texture are not loaded yet.",
    technical=TechnicalOut(
        evidence_type="survey",
        scale="Mapped soil unit at the field centre point",
        product="SSURGO map unit",
        indicator_id="ssurgo.map_unit.field_centre",
    ),
)

# The contract has no place for soil values yet, so these stay listed as not loaded.
SOIL_NOT_LOADED = ["How well it drains", "Organic matter", "Soil texture"]


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
        provenance=CROP_PROVENANCE,
    )


def _soil(record: FieldRecord) -> SectionOut[SoilOut]:
    if not record.soil_series or not record.soil_map_unit:
        return SectionOut[SoilOut](**NOT_LOADED)
    return SectionOut[SoilOut](
        status="available",
        data=SoilOut(
            series=record.soil_series,
            map_unit=record.soil_map_unit,
            sampling_note="Read at the centre point of the field, not averaged over its area.",
            not_loaded=SOIL_NOT_LOADED,
        ),
        provenance=SOIL_PROVENANCE,
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


def build_profile_view(record: FieldRecord, facts: IndicatorFacts) -> FieldProfileOut:
    return FieldProfileOut(
        field_id=record.field_id,
        crop_history=_crop_history(record),
        climate=_climate(facts),
        # No HLS greenness features exist yet (roadmap Phase 5), so there is nothing to show.
        vegetation=SectionOut[None](**NOT_LOADED),
        soil=_soil(record),
    )
