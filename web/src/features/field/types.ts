/** [longitude, latitude] in WGS84 (EPSG:4326), the order GeoJSON and MapLibre use. */
export type LonLat = readonly [number, number];

/** A closed ring: the first and last points are identical. */
export type Ring = readonly LonLat[];

export type CountyName = "Story" | "Boone";

export type FieldRole = "primary" | "test" | "drawn";

/**
 * What the field's recent crop history looks like. `rotation` fields are inside the
 * supported decision (a corn–soybean rotation); the rest are deliberate edge cases that
 * exercise "not enough evidence" (PRD §8.3).
 */
export type FieldClass = "rotation" | "corn" | "pasture" | "mixed" | "unknown";

export interface DemoField {
  id: string;
  role: FieldRole;
  county: CountyName;
  /** `demo` for every current field. `real` is reserved for boundaries a user supplies. */
  boundarySource: "demo" | "real" | "drawn";
  provenance: string;
  domainNote: string;
  fieldClass: FieldClass;
  coverDetail: string | null;
  /** Area in hectares as recorded by the data pipeline (30 m grid). */
  areaHa: number;
  centroid: LonLat;
  ring: Ring;
}

export interface County {
  county: CountyName;
  ring: Ring;
}
