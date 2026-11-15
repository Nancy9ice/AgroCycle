import { getFieldById } from "@/features/field/data";
import { apiBaseUrl } from "@/lib/api";
import { fetchProfile } from "./api-client";
import { buildCropHistory } from "./build-crop-history";
import profileSource from "./data/profile-source.generated.json";
import {
  sampleClimate,
  sampleVegetation,
  sampleVegetationProvenance,
} from "./data/sample-environment";
import type { FieldProfile, Provenance } from "./types";

const FIRST_YEAR = profileSource.firstYear;
const sources = profileSource.fields as Record<
  string,
  { cropSequence: string; soilSeries: string; soilMapUnit: string }
>;

const cropProvenance: Provenance = {
  title: "What was grown each year",
  whatItIs:
    "For each year, the crop that USDA's satellite-based crop map assigned to this field's squares.",
  source: "USDA NASS Cropland Data Layer",
  sourceUrl: "https://www.nass.usda.gov/Research_and_Science/Cropland/",
  precision:
    "30 m squares. It is USDA's best estimate from satellites, not a record kept by the farm, so agreeing with it is not independent proof. The map is sharper from 2024 (10 m), but 2024 and 2025 here use the 30 m version.",
  gaps: "Years before 2015 are not loaded.",
  technical: {
    evidenceType: "classified",
    scale: "30 m cells inside the field",
    product: "USDA NASS CDL 2015 to 2025",
    indicatorId: "cdl.crop_history.2015_2025",
  },
};

const soilProvenance: Provenance = {
  title: "The soil",
  whatItIs: "The soil type that USDA's soil survey maps at the centre of this field.",
  source: "USDA NRCS Soil Survey (SSURGO)",
  sourceUrl: "https://websoilsurvey.nrcs.usda.gov/app/",
  precision:
    "A mapped soil unit, not a soil test from this field. Only the point at the field's centre is read, not an average over the whole field.",
  gaps: "Drainage, organic matter and texture are not loaded yet.",
  technical: {
    evidenceType: "survey",
    scale: "Mapped soil unit at the field centre point",
    product: "SSURGO map unit",
    indicatorId: "ssurgo.map_unit.field_centre",
  },
};

/**
 * Builds the profile for one field. Returns undefined for unknown fields.
 *
 * - With `AGROCYCLE_API_URL` set, it asks the API (`GET /fields/{id}/profile`): real crop history and soil,
 *   weather when the indicator pipeline has produced it, and "not loaded" for anything else. A failing
 *   service throws `ServiceError`; it does not fall back quietly.
 * - Without it, it builds the profile locally. Crop history and soil are real (from the committed data
 *   files). Weather and greenness are labelled sample values until the pipeline and API exist.
 */
export async function getFieldProfile(
  fieldId: string,
): Promise<FieldProfile | undefined> {
  const baseUrl = apiBaseUrl();
  if (baseUrl) {
    if (!getFieldById(fieldId)) return undefined;
    return fetchProfile(baseUrl, fieldId);
  }

  const field = getFieldById(fieldId);
  const source = sources[fieldId];
  if (!field || !source) return undefined;

  return {
    fieldId,
    cropHistory: {
      status: "available",
      data: buildCropHistory(source.cropSequence, FIRST_YEAR),
      provenance: cropProvenance,
    },
    soil: {
      status: "available",
      data: {
        series: source.soilSeries,
        mapUnit: source.soilMapUnit,
        samplingNote:
          "Read at the centre point of the field, not averaged over its area.",
        notLoaded: ["How well it drains", "Organic matter", "Soil texture"],
      },
      provenance: soilProvenance,
    },
    climate: { status: "sample", data: sampleClimate, provenance: null },
    vegetation: {
      status: "sample",
      data: sampleVegetation,
      provenance: sampleVegetationProvenance,
    },
  };
}
