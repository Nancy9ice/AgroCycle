import type { County, CountyName, LonLat, Ring } from "./types";

const EARTH_RADIUS_M = 6_371_008.8;
const MIN_RING_POINTS = 4; // three corners plus the closing point

/** The size a drawn field may be. The API enforces the same limits (`api/core/validation.py`). */
export const MIN_FIELD_HA = 1;
export const MAX_FIELD_HA = 1000;
const ACRES_PER_HA = 2.47105;

export type GeometryIssueCode =
  | "not_closed"
  | "too_few_points"
  | "invalid_coordinate"
  | "self_intersection"
  | "outside_pilot_area"
  | "spans_counties"
  | "too_small"
  | "too_large";

export interface GeometryIssue {
  code: GeometryIssueCode;
  /** Plain-language message, safe to show to a farmer. */
  message: string;
}

export interface GeometryReport {
  valid: boolean;
  issues: readonly GeometryIssue[];
  /** Null when the ring is too broken to measure. */
  areaHa: number | null;
  /** The county all vertices fall in; null if outside the pilot area or spanning two. */
  county: CountyName | null;
}

const formatHa = (ha: number) =>
  new Intl.NumberFormat("en-GB", { maximumFractionDigits: ha < 10 ? 1 : 0 }).format(ha);
const formatAcres = (ha: number) =>
  new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(ha * ACRES_PER_HA);

/** Area of a ring in hectares, using a local flat projection (accurate for field sizes). */
export function ringAreaHa(ring: Ring): number {
  if (ring.length < MIN_RING_POINTS) return 0;
  const meanLat = ring.reduce((sum, [, lat]) => sum + lat, 0) / ring.length;
  const cosLat = Math.cos((meanLat * Math.PI) / 180);
  const toMetres = ([lon, lat]: LonLat): [number, number] => [
    ((lon * Math.PI) / 180) * EARTH_RADIUS_M * cosLat,
    ((lat * Math.PI) / 180) * EARTH_RADIUS_M,
  ];
  let twiceArea = 0;
  for (let i = 0; i < ring.length - 1; i += 1) {
    const [x1, y1] = toMetres(ring[i]);
    const [x2, y2] = toMetres(ring[i + 1]);
    twiceArea += x1 * y2 - x2 * y1;
  }
  return Math.abs(twiceArea) / 2 / 10_000;
}

/** Ray-casting point-in-polygon test. */
export function pointInRing([x, y]: LonLat, ring: Ring): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi)
      inside = !inside;
  }
  return inside;
}

function orientation(a: LonLat, b: LonLat, c: LonLat): number {
  return Math.sign((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]));
}

/** True when segments ab and cd properly cross (touching at shared endpoints does not count). */
function segmentsCross(a: LonLat, b: LonLat, c: LonLat, d: LonLat): boolean {
  const o1 = orientation(a, b, c);
  const o2 = orientation(a, b, d);
  const o3 = orientation(c, d, a);
  const o4 = orientation(c, d, b);
  return o1 !== 0 && o2 !== 0 && o3 !== 0 && o4 !== 0 && o1 !== o2 && o3 !== o4;
}

/** True when any two non-adjacent edges of the ring cross each other. */
export function hasSelfIntersection(ring: Ring): boolean {
  const edges = ring.length - 1;
  for (let i = 0; i < edges; i += 1) {
    for (let j = i + 2; j < edges; j += 1) {
      const sharesClosingVertex = i === 0 && j === edges - 1;
      if (sharesClosingVertex) continue;
      if (segmentsCross(ring[i], ring[i + 1], ring[j], ring[j + 1])) return true;
    }
  }
  return false;
}

const isFinitePoint = ([lon, lat]: LonLat) =>
  Number.isFinite(lon) &&
  Number.isFinite(lat) &&
  Math.abs(lon) <= 180 &&
  Math.abs(lat) <= 90;

/**
 * Checks a field boundary against the rules in PRD FR-01: it must be a closed, non-crossing
 * polygon inside one pilot county. Pure function, so it can validate demo, drawn and
 * uploaded boundaries alike.
 */
export function validateFieldGeometry(
  ring: Ring,
  counties: readonly County[],
): GeometryReport {
  const issues: GeometryIssue[] = [];

  if (ring.length < MIN_RING_POINTS) {
    issues.push({
      code: "too_few_points",
      message: "A boundary needs at least three corners.",
    });
    return { valid: false, issues, areaHa: null, county: null };
  }

  if (!ring.every(isFinitePoint)) {
    issues.push({
      code: "invalid_coordinate",
      message: "Some points are not valid longitude and latitude values.",
    });
    return { valid: false, issues, areaHa: null, county: null };
  }

  const first = ring[0];
  const last = ring[ring.length - 1];
  if (first[0] !== last[0] || first[1] !== last[1]) {
    issues.push({
      code: "not_closed",
      message: "The boundary is not closed: the last point must return to the first.",
    });
  }

  if (hasSelfIntersection(ring)) {
    issues.push({
      code: "self_intersection",
      message: "The boundary crosses itself. Move a corner so the edges do not cross.",
    });
  }

  // A crossing or unclosed outline has no meaningful area, so size is judged only on a clean shape.
  const area = ringAreaHa(ring);
  if (!issues.some((i) => i.code === "not_closed" || i.code === "self_intersection")) {
    if (area < MIN_FIELD_HA) {
      issues.push({
        code: "too_small",
        message: `This boundary is only about ${formatHa(area)} hectares. A field here needs at least ${MIN_FIELD_HA} hectare, so check that you marked all the corners.`,
      });
    } else if (area > MAX_FIELD_HA) {
      issues.push({
        code: "too_large",
        message: `This boundary is about ${formatHa(area)} hectares (${formatAcres(area)} acres), far larger than one field. A boundary here can be up to ${formatHa(MAX_FIELD_HA)} hectares (about ${formatAcres(MAX_FIELD_HA)} acres). Mark just one field.`,
      });
    }
  }

  const countiesHit = new Set<CountyName>();
  let anyOutside = false;
  for (const point of ring) {
    const hit = counties.find((county) => pointInRing(point, county.ring));
    if (hit) countiesHit.add(hit.county);
    else anyOutside = true;
  }

  let county: CountyName | null = null;
  if (anyOutside) {
    issues.push({
      code: "outside_pilot_area",
      message:
        "Part of the boundary is outside Story and Boone counties, Iowa, the pilot area.",
    });
  } else if (countiesHit.size > 1) {
    issues.push({
      code: "spans_counties",
      message: "The boundary crosses a county line. Choose a field inside one county.",
    });
  } else {
    county = [...countiesHit][0] ?? null;
  }

  return { valid: issues.length === 0, issues, areaHa: area, county };
}
