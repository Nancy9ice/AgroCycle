import type { LonLat } from "./types";

/** The biggest file we will read, and the most points one field may have (the API's limit as well). */
export const MAX_FILE_BYTES = 1_000_000;
export const MAX_FILE_VERTICES = 2000;

export type BoundaryFileResult =
  | {
      ok: true;
      /** The corners, without the closing point, in the order the file gave them. */
      corners: LonLat[];
    }
  | { ok: false; message: string };

const fail = (message: string): BoundaryFileResult => ({ ok: false, message });

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

/** The geometry object inside a Feature, a one-feature FeatureCollection, or the geometry itself. */
function geometryOf(root: Record<string, unknown>): Record<string, unknown> | string {
  if (root.type === "FeatureCollection") {
    const features = Array.isArray(root.features) ? root.features : [];
    if (features.length === 0) return "The file has no shapes in it.";
    if (features.length > 1) {
      return `The file has ${features.length} shapes. Upload one field per file.`;
    }
    const only = features[0];
    return isRecord(only) && isRecord(only.geometry)
      ? only.geometry
      : "The shape in the file has no boundary.";
  }
  if (root.type === "Feature") {
    return isRecord(root.geometry)
      ? root.geometry
      : "The shape in the file has no boundary.";
  }
  return root;
}

/**
 * Reads a GeoJSON boundary from a file's text. It accepts exactly one polygon in WGS 84 (longitude and latitude),
 * as a Polygon, a one-polygon MultiPolygon, a Feature, or a one-feature collection, and says plainly what is wrong
 * with anything else. It does not judge whether the boundary is a good one: the same checks as for a drawn boundary
 * do that (inside the pilot area, not crossing itself, a sensible size).
 */
export function parseBoundaryFile(text: string): BoundaryFileResult {
  let root: unknown;
  try {
    root = JSON.parse(text);
  } catch {
    return fail(
      "That file could not be read as GeoJSON. Export your field as a .geojson file and try again.",
    );
  }
  if (!isRecord(root)) return fail("That file is not a GeoJSON boundary.");

  // Old GeoJSON can name a different coordinate system. Anything but WGS 84 would put the field in the wrong place.
  const crs =
    isRecord(root.crs) && isRecord(root.crs.properties)
      ? String(root.crs.properties.name ?? "")
      : "";
  if (crs !== "" && !/4326|CRS84/i.test(crs)) {
    return fail(
      "This file uses a coordinate system other than WGS 84. Export it as WGS 84 (EPSG:4326) and try again.",
    );
  }

  const geometry = geometryOf(root);
  if (typeof geometry === "string") return fail(geometry);

  let rings: unknown;
  if (geometry.type === "Polygon") {
    rings = geometry.coordinates;
  } else if (geometry.type === "MultiPolygon") {
    const polygons = Array.isArray(geometry.coordinates) ? geometry.coordinates : [];
    if (polygons.length !== 1) {
      return fail(
        `The file has ${polygons.length} separate areas. Upload one field per file.`,
      );
    }
    rings = polygons[0];
  } else {
    return fail(
      `A boundary must be a polygon, but this file has a ${String(geometry.type)}.`,
    );
  }

  if (!Array.isArray(rings) || rings.length === 0 || !Array.isArray(rings[0])) {
    return fail("The boundary in the file is empty.");
  }
  if (rings.length > 1) {
    return fail(
      "This boundary has a hole in it. Remove the hole, or upload just the outer edge of the field.",
    );
  }
  const outer = rings[0] as unknown[];
  if (outer.length > MAX_FILE_VERTICES) {
    return fail(
      `This boundary has ${outer.length} points. The limit is ${MAX_FILE_VERTICES}; simplify it and try again.`,
    );
  }

  const points: LonLat[] = [];
  for (const position of outer) {
    if (!Array.isArray(position) || position.length < 2) {
      return fail("Some points in the file are not valid positions.");
    }
    const [lon, lat] = position as unknown[];
    if (
      typeof lon !== "number" ||
      typeof lat !== "number" ||
      !Number.isFinite(lon) ||
      !Number.isFinite(lat)
    ) {
      return fail("Some points in the file are not valid numbers.");
    }
    if (Math.abs(lon) > 180 || Math.abs(lat) > 90) {
      return fail(
        "These coordinates look like metres, not longitude and latitude. Export the boundary as WGS 84 (EPSG:4326) and try again.",
      );
    }
    points.push([lon, lat]);
  }

  // The closing point repeats the first; a drawn boundary does not carry it.
  const first = points[0];
  const last = points[points.length - 1];
  const closed = points.length > 1 && first[0] === last[0] && first[1] === last[1];
  const corners = closed ? points.slice(0, -1) : points;
  if (corners.length < 3) return fail("A boundary needs at least three corners.");
  return { ok: true, corners };
}

/** A zoom level that fits the boundary on the map: about a kilometre across gives 14, ten kilometres gives 11. */
export function zoomFor(corners: readonly LonLat[]): number {
  const lons = corners.map((c) => c[0]);
  const lats = corners.map((c) => c[1]);
  const extent = Math.max(
    Math.max(...lons) - Math.min(...lons),
    Math.max(...lats) - Math.min(...lats),
    1e-6,
  );
  return Math.min(17, Math.max(9, Math.round(Math.log2(360 / extent)) - 1));
}

export const centreOf = (corners: readonly LonLat[]): LonLat => {
  const lons = corners.map((c) => c[0]);
  const lats = corners.map((c) => c[1]);
  return [
    (Math.min(...lons) + Math.max(...lons)) / 2,
    (Math.min(...lats) + Math.max(...lats)) / 2,
  ];
};
