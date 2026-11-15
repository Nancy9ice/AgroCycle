import { ServiceError, apiBaseUrl, callApi } from "@/lib/api";

/**
 * One read from the API for a page section, as a value the page can show instead of crashing.
 *
 * - `ok`: the data.
 * - `no_service`: `AGROCYCLE_API_URL` is not set, so this copy of the site has no backend.
 * - `not_found`: the API says it does not have it (404).
 * - `not_loaded`: the API has not been given the data yet (503).
 * - `unreachable`: the service is down or sent something unusable.
 */
export type ApiRead<T> =
  | { status: "ok"; data: T }
  | { status: "no_service" }
  | { status: "not_found" }
  | { status: "not_loaded" }
  | { status: "unreachable" };

export async function readApi<T>(path: string): Promise<ApiRead<T>> {
  const baseUrl = apiBaseUrl();
  if (!baseUrl) return { status: "no_service" };
  try {
    const body = await callApi(baseUrl, path);
    return body === undefined
      ? { status: "not_found" }
      : { status: "ok", data: body as T };
  } catch (error) {
    if (error instanceof ServiceError) {
      return { status: error.status === 503 ? "not_loaded" : "unreachable" };
    }
    throw error;
  }
}

/** Plain-language text for a read that did not return data, for a page to show in place of it. */
export const readNotice: Record<Exclude<ApiRead<unknown>["status"], "ok">, string> = {
  no_service:
    "This copy of the site is not connected to the data service, so this page has nothing to show.",
  not_found: "The data service does not have this.",
  not_loaded: "The data service has not been given this yet.",
  unreachable: "The data service could not be reached. Try again in a moment.",
};
