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
 * Calls the API and returns the parsed JSON, or `undefined` if the API says the thing does not exist
 * (404). Anything else that goes wrong throws `ServiceError`: an unreachable service, an error status or a
 * body that is not JSON. A broken service must be visible, never a silent guess.
 */
export async function callApi(
  baseUrl: string,
  path: string,
  init: { method?: "GET" | "POST"; body?: unknown; timeoutMs?: number } = {},
): Promise<unknown | undefined> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method: init.method ?? "GET",
      headers:
        init.body === undefined ? undefined : { "content-type": "application/json" },
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
      cache: "no-store",
      signal: AbortSignal.timeout(init.timeoutMs ?? 10_000),
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
