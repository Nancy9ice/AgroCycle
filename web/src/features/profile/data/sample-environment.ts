/**
 * SAMPLE VALUES. Weather (NASA POWER) and greenness (NASA HLS) are not in the data pipeline
 * yet (roadmap Phases 4 and 5), so the profile screen shows these placeholders, labelled as
 * sample in the UI. They are the same for every field and are not results.
 * Delete this file when the API serves the real indicators.
 */
import type { ClimateProfile, Provenance, VegetationProfile } from "../types";

const powerSource = {
  source: "NASA POWER",
  sourceUrl: "https://power.larc.nasa.gov/",
  precision:
    "Covers an area about 50 km across (a grid of 0.5° by 0.625°), so your field's own weather could be a bit different. It is a model-based estimate, not a weather station on the field.",
  gaps: "Days with missing data are skipped.",
};

function power(
  title: string,
  whatItIs: string,
  variable: string,
  indicatorId: string,
): Provenance {
  return {
    title,
    whatItIs,
    ...powerSource,
    technical: {
      evidenceType: "model_reanalysis",
      scale: "Grid 0.5° × 0.625° (about 50 km)",
      variable,
      indicatorId,
      version: "Not recorded: sample values",
    },
  };
}

export const sampleClimate: ClimateProfile = {
  periodLabel: "Sample values",
  indicators: [
    {
      id: "gs-rain",
      label: "Rain while crops grow (April to September)",
      value: "612 mm",
      context: "About 24 inches, added up for each year and then averaged.",
      provenance: power(
        "Rain while crops grow",
        "All the rain from April to September, added up for each year, then averaged over the years.",
        "PRECTOTCORR (daily)",
        "sample.power.gs_precip_total",
      ),
    },
    {
      id: "hot-days",
      label: "Very hot days (above 32 °C / 90 °F)",
      value: "9 a year",
      context: "Mostly in July, when corn flowers.",
      provenance: power(
        "Very hot days",
        "The number of days a year when the highest air temperature was above 32 °C, averaged over the years.",
        "T2M_MAX (daily)",
        "sample.power.hot_days",
      ),
    },
    {
      id: "dry-spells",
      label: "Dry spells of 10 or more days with no rain",
      value: "1 to 2 a season",
      context: "April to September.",
      provenance: power(
        "Dry spells",
        "Runs of 10 or more days in a row with almost no rain, counted from April to September and averaged over the years.",
        "PRECTOTCORR (daily)",
        "sample.power.dry_spells_10d",
      ),
    },
    {
      id: "gdd",
      label: "Warmth for crop growth",
      value: "1,580",
      context: "Growing degree days, May to September. Enough warmth for corn.",
      provenance: power(
        "Warmth for crop growth",
        "Growing degree days add up how much warmth crops got each day, from May to September, averaged over the years.",
        "T2M_MAX, T2M_MIN (daily)",
        "sample.power.gdd_may_sep",
      ),
    },
  ],
};

export const sampleVegetationProvenance: Provenance = {
  title: "How green the field is through the year",
  whatItIs:
    "A greenness index (NDVI) for each month, from satellite images of this field. Tall values mean plants are growing; low values mean mostly bare soil.",
  source: "NASA Harmonized Landsat Sentinel-2 (HLS)",
  sourceUrl: "https://hls.gsfc.nasa.gov/",
  precision:
    "30 m squares, cloud-screened. Greenness is not yield and not a soil measurement, and it cannot tell crop from weeds or crop residue.",
  gaps: "Months with too few clear images are marked “don't know”, not guessed.",
  technical: {
    evidenceType: "derived",
    scale: "30 m, field scale",
    product: "HLS surface reflectance, quality mask applied",
    variable: "NDVI",
    indicatorId: "sample.hls.ndvi_monthly",
    version: "Not recorded: sample values",
  },
};

export const sampleVegetation: VegetationProfile = {
  months: [
    { month: 1, ndvi: null, clearImages: 1, state: "unknown" },
    { month: 2, ndvi: null, clearImages: 2, state: "unknown" },
    { month: 3, ndvi: 0.15, clearImages: 4, state: "bare" },
    { month: 4, ndvi: 0.22, clearImages: 5, state: "bare" },
    { month: 5, ndvi: 0.25, clearImages: 6, state: "bare" },
    { month: 6, ndvi: 0.72, clearImages: 5, state: "growing" },
    { month: 7, ndvi: 0.86, clearImages: 4, state: "growing" },
    { month: 8, ndvi: 0.82, clearImages: 5, state: "growing" },
    { month: 9, ndvi: 0.6, clearImages: 6, state: "growing" },
    { month: 10, ndvi: 0.28, clearImages: 5, state: "bare" },
    { month: 11, ndvi: 0.2, clearImages: 4, state: "bare" },
    { month: 12, ndvi: null, clearImages: 2, state: "unknown" },
  ],
  interpretation:
    "After harvest in October the soil sits mostly bare until crops come up in June. That is the gap a cover crop such as red clover or alfalfa could fill.",
  unknownReason:
    "From December to February snow and cloud hide the field in most images, so we do not guess whether the soil is bare.",
  barePrinciple: "A month counts as bare when its greenness index is below 0.3.",
};
