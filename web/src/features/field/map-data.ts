import type { DemoField, LonLat, Ring } from "./types";

/** How a field is drawn on the map and listed: the primary demo, a rotation test, or an edge case. */
export type MarkerKind = "primary" | "rotation" | "edge";

export const markerKind = (field: DemoField): MarkerKind =>
  field.role === "primary"
    ? "primary"
    : field.fieldClass === "rotation"
      ? "rotation"
      : "edge";

type Bounds = [west: number, south: number, east: number, north: number];

export function ringBounds(rings: readonly Ring[]): Bounds {
  const points = rings.flat();
  const lons = points.map(([lon]) => lon);
  const lats = points.map(([, lat]) => lat);
  return [Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)];
}

const properties = (field: DemoField) => ({
  id: field.id,
  county: field.county,
  kind: markerKind(field),
});

export function fieldPolygons(fields: readonly DemoField[]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: fields.map((field) => ({
      type: "Feature",
      properties: properties(field),
      geometry: {
        type: "Polygon",
        coordinates: [field.ring.map((p): number[] => [...p])],
      },
    })),
  };
}

export function fieldPoints(fields: readonly DemoField[]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: fields.map((field) => ({
      type: "Feature",
      properties: properties(field),
      geometry: { type: "Point", coordinates: [...field.centroid] },
    })),
  };
}

export function ringsToPolygons(rings: readonly Ring[]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: rings.map((ring) => ({
      type: "Feature",
      properties: {},
      geometry: { type: "Polygon", coordinates: [ring.map((p): number[] => [...p])] },
    })),
  };
}

export const emptyCollection: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [],
};

export type { Bounds, LonLat };
