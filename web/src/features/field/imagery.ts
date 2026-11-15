/**
 * The aerial photo of a demonstration field (NAIP, from DE's `naip_tiles`). One photo from one flight date,
 * reference imagery for looking at the field, never crop ground truth. The API checks the photo against its
 * checksum and lays it on the ground; this file is the web side of that contract.
 */

export interface ImageryTile {
  tile_id: string;
  flight_date: string; // YYYY-MM-DD
}

export interface FieldImagery {
  field_id: string;
  year: number;
  tiles: readonly ImageryTile[];
  resolution_m: number;
  /** West, south, east, north of the picture as drawn, longitude and latitude. */
  bounds: readonly [number, number, number, number];
  evidence_type: string;
  attribution: string;
  note: string;
}

const isFiniteNumber = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

/**
 * Reads the API's answer. Returns `null` for "no photo" and for anything that does not look right, so a
 * malformed answer hides the toggle instead of placing a picture at made-up coordinates.
 */
export function parseImagery(body: unknown): FieldImagery | null {
  if (typeof body !== "object" || body === null) return null;
  const b = body as Record<string, unknown>;
  if (b.available !== true) return null;
  const { bounds, tiles } = b;
  if (!Array.isArray(bounds) || bounds.length !== 4 || !bounds.every(isFiniteNumber)) {
    return null;
  }
  const [west, south, east, north] = bounds as number[];
  if (west >= east || south >= north) return null;
  if (west < -180 || east > 180 || south < -90 || north > 90) return null;
  if (!Array.isArray(tiles) || tiles.length === 0) return null;
  const validTiles = tiles.every(
    (tile) =>
      typeof tile === "object" &&
      tile !== null &&
      typeof (tile as ImageryTile).tile_id === "string" &&
      /^\d{4}-\d{2}-\d{2}$/.test((tile as ImageryTile).flight_date),
  );
  if (!validTiles) return null;
  if (
    typeof b.field_id !== "string" ||
    !isFiniteNumber(b.year) ||
    !isFiniteNumber(b.resolution_m) ||
    typeof b.evidence_type !== "string" ||
    typeof b.attribution !== "string" ||
    typeof b.note !== "string"
  ) {
    return null;
  }
  return {
    field_id: b.field_id,
    year: b.year,
    tiles: tiles as ImageryTile[],
    resolution_m: b.resolution_m,
    bounds: [west, south, east, north],
    evidence_type: b.evidence_type,
    attribution: b.attribution,
    note: b.note,
  };
}

const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
] as const;

function parts(isoDate: string): { day: number; month: number; year: number } {
  const [year, month, day] = isoDate.split("-").map(Number);
  return { day, month, year };
}

/**
 * When the photo was taken, in words. A field cut from two tiles can have two flight dates, and the photo
 * must say so rather than imply one: "5 August 2025", or "5 August and 14 September 2025".
 */
export function flightLabel(tiles: readonly ImageryTile[]): string {
  const dates = [...new Set(tiles.map((tile) => tile.flight_date))].sort();
  if (dates.length === 0) return "";
  const all = dates.map(parts);
  const text = (d: (typeof all)[number], withYear: boolean) =>
    `${d.day} ${MONTHS[d.month - 1]}${withYear ? ` ${d.year}` : ""}`;
  if (all.length === 1) return text(all[0], true);
  const sameYear = all.every((d) => d.year === all[0].year);
  const shown = all.map((d, i) => text(d, !sameYear || i === all.length - 1));
  return `${shown.slice(0, -1).join(", ")} and ${shown[shown.length - 1]}`;
}

export const imageryUrl = (fieldId: string) =>
  `/field-imagery/${encodeURIComponent(fieldId)}`;
export const imageryImageUrl = (fieldId: string) => `${imageryUrl(fieldId)}/image`;
