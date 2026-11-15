import { ServiceError, callApi } from "@/lib/api";
import type { FieldProfile } from "./types";

/**
 * Calls the API's `GET /fields/{id}/profile` (see `api/README.md`). The API returns the `FieldProfile`
 * contract in `types.ts`, camelCase, with only real values: a section with nothing behind it is
 * `not_loaded`. The API never sends the status `sample`; that label belongs to the local stand-in.
 */

const STATUSES = ["available", "not_loaded"];
const SECTIONS = ["cropHistory", "climate", "vegetation", "soil"] as const;

function isFieldProfile(value: unknown): value is FieldProfile {
  if (typeof value !== "object" || value === null) return false;
  const profile = value as Record<string, unknown>;
  if (typeof profile.fieldId !== "string") return false;
  return SECTIONS.every((name) => {
    const section = profile[name] as { status?: unknown; data?: unknown } | undefined;
    return (
      typeof section === "object" &&
      section !== null &&
      typeof section.status === "string" &&
      STATUSES.includes(section.status) &&
      "data" in section &&
      // A section that says it has data must carry some.
      (section.status !== "available" ||
        (typeof section.data === "object" && section.data !== null))
    );
  });
}

/** Returns the API's profile, `undefined` if the field does not exist, and throws `ServiceError` otherwise. */
export async function fetchProfile(
  baseUrl: string,
  fieldId: string,
): Promise<FieldProfile | undefined> {
  const body = await callApi(baseUrl, `/fields/${encodeURIComponent(fieldId)}/profile`);
  if (body === undefined) return undefined;
  if (!isFieldProfile(body)) {
    throw new ServiceError("The profile service sent an unexpected answer.");
  }
  return body;
}
