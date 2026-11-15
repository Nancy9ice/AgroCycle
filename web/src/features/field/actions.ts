"use server";

import { ServiceError, apiBaseUrl, callApi } from "@/lib/api";

export type SaveBoundaryResult =
  { ok: true; fieldId: string } | { ok: false; message: string };

export type SaveCropHistoryResult =
  { ok: true; fieldClass: string; summary: string } | { ok: false; message: string };

const unavailable =
  "This copy of the site is not connected to the data service, so it cannot keep your boundary.";

/**
 * Keeps a boundary the farmer drew, so they can carry on to a profile for it (`POST /fields/drawn`). Called only
 * when they choose to continue: until then the boundary has not left their device. The API validates again.
 */
export async function saveDrawnBoundary(
  ring: readonly (readonly [number, number])[],
): Promise<SaveBoundaryResult> {
  const baseUrl = apiBaseUrl();
  if (!baseUrl) return { ok: false, message: unavailable };
  try {
    const body = (await callApi(baseUrl, "/fields/drawn", {
      method: "POST",
      body: { geometry: { type: "Polygon", coordinates: [ring] } },
    })) as
      { valid: boolean; field_id: string; errors: { message: string }[] } | undefined;
    if (!body) return { ok: false, message: "The service could not keep your boundary." };
    if (!body.valid) {
      return {
        ok: false,
        message: body.errors[0]?.message ?? "This boundary could not be accepted.",
      };
    }
    return { ok: true, fieldId: body.field_id };
  } catch (error) {
    return { ok: false, message: failure(error) };
  }
}

/** The farmer's own crop for each of the 11 seasons, oldest first (`POST /fields/{id}/crop-history`). */
export async function saveCropHistory(
  fieldId: string,
  crops: readonly string[],
): Promise<SaveCropHistoryResult> {
  const baseUrl = apiBaseUrl();
  if (!baseUrl) return { ok: false, message: unavailable };
  try {
    const body = (await callApi(
      baseUrl,
      `/fields/${encodeURIComponent(fieldId)}/crop-history`,
      {
        method: "POST",
        body: { crops },
      },
    )) as { field_class: string; summary: string } | undefined;
    if (!body) return { ok: false, message: "We could not find this field." };
    return { ok: true, fieldClass: body.field_class, summary: body.summary };
  } catch (error) {
    return { ok: false, message: failure(error) };
  }
}

function failure(error: unknown): string {
  if (error instanceof ServiceError) {
    if (error.status === 429)
      return "Too many boundaries were saved just now. Try again in a little while.";
    if (error.status === 422)
      return "Those answers could not be accepted. Check every season has a crop.";
    return "The data service could not be reached. Try again in a moment.";
  }
  return "Something went wrong. Try again.";
}
