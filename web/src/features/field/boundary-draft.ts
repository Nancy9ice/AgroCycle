import type { County, LonLat, Ring } from "./types";
import { pointInRing, validateFieldGeometry, type GeometryReport } from "./geometry";

export const ACRES_PER_HECTARE = 2.47105;
export const MIN_CORNERS = 3;

/** The corners a farmer tapped, closed into the ring the validator expects. Fewer than three gives []. */
export function ringFromCorners(corners: readonly LonLat[]): Ring {
  if (corners.length < MIN_CORNERS) return [];
  return [...corners, corners[0]];
}

/** The FR-01 checks on a drawn boundary. Pure, so the screen never decides validity itself. */
export function checkDraftBoundary(
  corners: readonly LonLat[],
  counties: readonly County[],
): GeometryReport {
  return validateFieldGeometry(ringFromCorners(corners), counties);
}

/** Acres first: that is the unit farmers in Iowa use. Hectares follow for the adviser. */
export function describeArea(areaHa: number): string {
  const acres = areaHa * ACRES_PER_HECTARE;
  const roundedAcres = acres < 10 ? acres.toFixed(1) : Math.round(acres).toString();
  const roundedHa = areaHa < 10 ? areaHa.toFixed(1) : Math.round(areaHa).toString();
  return `${roundedAcres} acres (${roundedHa} ha)`;
}

export type LocationOutcome =
  { kind: "inside"; county: string; approximate: boolean } | { kind: "outside" };

/** Radius above which a phone's position is too rough to place a field by. */
export const APPROXIMATE_ABOVE_M = 500;

/** Where a position falls in the pilot area. Nothing here leaves the browser. */
export function locateInPilot(
  position: LonLat,
  accuracyM: number | null,
  counties: readonly County[],
): LocationOutcome {
  const hit = counties.find((county) => pointInRing(position, county.ring));
  if (!hit) return { kind: "outside" };
  return {
    kind: "inside",
    county: hit.county,
    approximate: accuracyM !== null && accuracyM > APPROXIMATE_ABOVE_M,
  };
}

/** A browser position error in a farmer's words, with what to do next. */
export function locationErrorMessage(code: number | "unsupported"): string {
  if (code === "unsupported")
    return "This browser cannot share your location. Find your field on the map instead.";
  if (code === 1)
    return "Location is turned off for this site. You can allow it in your browser settings, or find your field on the map.";
  if (code === 3)
    return "Finding your location took too long. Try again, or find your field on the map.";
  return "We could not find your location. Check that location is turned on for your device and browser, then try again, or find your field on the map.";
}

const PRECISE = {
  enableHighAccuracy: true,
  timeout: 15_000,
  maximumAge: 60_000,
} as const;
const ROUGH = {
  enableHighAccuracy: false,
  timeout: 10_000,
  maximumAge: 300_000,
} as const;

type Locator = Pick<Geolocation, "getCurrentPosition">;

/**
 * Asks the device where it is. A precise position first; if the device cannot give one (many desktops have no
 * GPS) or takes too long, one more ask for a rough position, which a Wi-Fi or network fix can answer. A refusal
 * is final: asking again cannot change a person's mind. The rough position is flagged by its accuracy, so the
 * screen still tells the farmer to check the map is on their field.
 */
export function findPosition(
  geolocation: Locator,
  onFound: PositionCallback,
  onFailed: PositionErrorCallback,
): void {
  geolocation.getCurrentPosition(
    onFound,
    (error) => {
      if (error.code === 1) return onFailed(error);
      geolocation.getCurrentPosition(onFound, onFailed, ROUGH);
    },
    PRECISE,
  );
}
