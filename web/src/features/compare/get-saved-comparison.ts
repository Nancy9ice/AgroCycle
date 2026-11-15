import { loadField } from "@/features/field/data/load";
import { ServiceError, apiBaseUrl, callApi } from "@/lib/api";
import { isCompareResponse } from "./api-client";
import type { Comparison } from "./get-comparison";
import { withPlainWords } from "./get-comparison";

/**
 * A comparison the API stored, opened from its share link (`GET /analyses/{id}`). The stored result is shown
 * exactly as it was run: the same decision, rules version and data version. It is not recomputed, so a link
 * sent to an adviser keeps showing what the farmer saw even after the data is reloaded.
 *
 * Returns undefined when there is no such analysis, or no API to ask. A failing service throws `ServiceError`.
 */
export async function getSavedComparison(
  analysisId: string,
): Promise<Comparison | undefined> {
  const baseUrl = apiBaseUrl();
  if (!baseUrl) return undefined;

  const body = await callApi(baseUrl, `/analyses/${encodeURIComponent(analysisId)}`);
  if (body === undefined) return undefined;
  if (!isCompareResponse(body)) {
    throw new ServiceError("The comparison service sent an unexpected answer.");
  }

  const fieldId = (body as { field?: { field_id?: string } }).field?.field_id;
  const field = fieldId ? await loadField(fieldId) : undefined;
  if (!field) return undefined;

  return {
    field,
    decision: withPlainWords(body.decision),
    preview: body.preview,
    analysisId: body.analysis_id ?? analysisId,
    context: body.context_recorded,
    contextNote: body.context_note,
    saved: true,
    provenance: {
      source: "api",
      rulesVersion: body.decision.rules_version,
      dataVersion: body.data_version || undefined,
      createdAt: body.created_at,
    },
  };
}
