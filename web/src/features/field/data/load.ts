import { cache } from "react";
import { apiBaseUrl, callApi, ServiceError } from "@/lib/api";
import { counties as localCounties, demoFields as localFields } from "./index";
import type { County, CountyName, DemoField, FieldClass, Ring } from "../types";

/**
 * The demonstration fields and the pilot-area outlines, for server components.
 *
 * With `AGROCYCLE_API_URL` set they come from the API (`GET /fields/demo`, `GET /meta/pilot-area`) and a
 * failing service throws `ServiceError`. Without it they come from the generated files, so the app still
 * runs with no backend. `cache` shares one read per request.
 */
export interface FieldData {
  fields: readonly DemoField[];
  counties: readonly County[];
}

interface ApiDemoField {
  field_id: string;
  county: CountyName;
  role: "primary" | "test";
  boundary_source: "demo" | "real";
  area_ha: number;
  geometry: { coordinates: number[][][] };
  field_class: string | null;
  domain_note: string;
  provenance: string;
  cover_detail: string | null;
  centroid: [number, number];
}

interface ApiPilotArea {
  counties: { county: CountyName; ring: number[][] }[];
}

/** DS1's class names (what the engine reads) to the labels the screens use. */
const DISPLAY_CLASS: Record<string, FieldClass> = {
  rotation: "rotation",
  continuous_corn: "corn",
  pasture_hay: "pasture",
  mixed: "mixed",
  other: "mixed",
};

export function fromApiField(item: ApiDemoField): DemoField {
  return {
    id: item.field_id,
    role: item.role,
    county: item.county,
    boundarySource: item.boundary_source,
    provenance: item.provenance,
    domainNote: item.domain_note,
    fieldClass: DISPLAY_CLASS[item.field_class ?? ""] ?? "mixed",
    coverDetail: item.cover_detail,
    areaHa: item.area_ha,
    centroid: item.centroid,
    ring: item.geometry.coordinates[0] as unknown as Ring,
  };
}

export const loadFieldData = cache(async (): Promise<FieldData> => {
  const baseUrl = apiBaseUrl();
  if (!baseUrl) return { fields: localFields, counties: localCounties };

  const [fields, area] = await Promise.all([
    callApi(baseUrl, "/fields/demo"),
    callApi(baseUrl, "/meta/pilot-area"),
  ]);
  if (!Array.isArray(fields) || !area) {
    throw new ServiceError("The service sent an unexpected answer.");
  }
  return {
    fields: (fields as ApiDemoField[]).map(fromApiField),
    counties: (area as ApiPilotArea).counties.map((c) => ({
      county: c.county,
      ring: c.ring as unknown as Ring,
    })),
  };
});

export async function loadField(id: string): Promise<DemoField | undefined> {
  const { fields } = await loadFieldData();
  return fields.find((field) => field.id === id);
}
