/**
 * Server-side access to the AgroCycle API (`../api`, see `api/README.md`).
 *
 * `AGROCYCLE_API_URL` is deliberately not a `NEXT_PUBLIC_` variable: the Next.js server calls the API and
 * the browser never does, so no CORS or key handling is needed. When it is unset the app uses its local
 * stand-ins, so it still runs with no backend.
 */

export class ServiceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ServiceError";
  }
}

export const apiBaseUrl = (): string | undefined => {
  const base = process.env.AGROCYCLE_API_URL?.replace(/\/+$/, "");
  if (!base) return undefined;
  return base.endsWith("/api/v1") ? base : `${base}/api/v1`;
};

/**
 * Whether this server may answer a comparison with the web app's own TypeScript copy of the decision
 * engine when no API is configured.
 *
 * The API (`engine/` run by FastAPI) is the one authoritative engine. The copy exists so the app can run
 * on a laptop with no backend, and `engine-parity.test.ts` keeps it equal to the real one, but it also
 * works from a thinner profile (no weather, no drainage), so its answer is never the same as the API's
 * for a real field. Outside production it is allowed. In production it must be switched on on purpose
 * (`AGROCYCLE_ALLOW_OFFLINE_ENGINE=true`), so a deployment that forgot `AGROCYCLE_API_URL` fails loudly
 * instead of quietly showing offline answers as if they were the service's.
 */
export const offlineEngineAllowed = (): boolean =>
  process.env.NODE_ENV !== "production" ||
  process.env.AGROCYCLE_ALLOW_OFFLINE_ENGINE === "true";

/**
 * Calls the API and returns the parsed JSON, or `undefined` if the API says the thing does not exist
 * (404). Anything else that goes wrong throws `ServiceError`: an unreachable service, an error status or a
 * body that is not JSON. A broken service must be visible, never a silent guess.
 */
export async function callApi(
  baseUrl: string,
  path: string,
  init: { method?: "GET" | "POST"; body?: unknown } = {},
): Promise<unknown | undefined> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method: init.method ?? "GET",
      headers:
        init.body === undefined ? undefined : { "content-type": "application/json" },
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
  } catch {
    throw new ServiceError("The service could not be reached.");
  }

  if (response.status === 404) return undefined;
  if (!response.ok) {
    throw new ServiceError(`The service answered with an error (${response.status}).`);
  }
  try {
    return await response.json();
  } catch {
    throw new ServiceError("The service sent an unexpected answer.");
  }
}
