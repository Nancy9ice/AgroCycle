import { describe, expect, it } from "vitest";
import { counties, demoFields } from "./data";
import {
  hasSelfIntersection,
  pointInRing,
  ringAreaHa,
  validateFieldGeometry,
} from "./geometry";
import type { Ring } from "./types";

// A small square in Story County, about 0.01° (roughly 0.8 km × 1.1 km).
const square: Ring = [
  [-93.5, 42.0],
  [-93.49, 42.0],
  [-93.49, 42.01],
  [-93.5, 42.01],
  [-93.5, 42.0],
];

describe("validateFieldGeometry", () => {
  it("accepts a valid polygon inside one county and reports its county", () => {
    const report = validateFieldGeometry(square, counties);
    expect(report.valid).toBe(true);
    expect(report.issues).toEqual([]);
    expect(report.county).toBe("Story");
    expect(report.areaHa).toBeGreaterThan(80);
    expect(report.areaHa).toBeLessThan(100);
  });

  it("rejects a ring with too few points", () => {
    const report = validateFieldGeometry(square.slice(0, 3), counties);
    expect(report.valid).toBe(false);
    expect(report.issues[0].code).toBe("too_few_points");
    expect(report.areaHa).toBeNull();
  });

  it("rejects an unclosed ring", () => {
    const report = validateFieldGeometry(square.slice(0, 4), counties);
    expect(report.issues.map((issue) => issue.code)).toContain("not_closed");
  });

  it("rejects a bow-tie that crosses itself", () => {
    const bowTie: Ring = [
      [-93.5, 42.0],
      [-93.49, 42.01],
      [-93.49, 42.0],
      [-93.5, 42.01],
      [-93.5, 42.0],
    ];
    expect(hasSelfIntersection(bowTie)).toBe(true);
    expect(validateFieldGeometry(bowTie, counties).issues.map((i) => i.code)).toContain(
      "self_intersection",
    );
  });

  it("does not flag a valid L-shaped polygon as self-crossing", () => {
    const lShape: Ring = [
      [-93.5, 42.0],
      [-93.49, 42.0],
      [-93.49, 42.005],
      [-93.495, 42.005],
      [-93.495, 42.01],
      [-93.5, 42.01],
      [-93.5, 42.0],
    ];
    expect(hasSelfIntersection(lShape)).toBe(false);
  });

  it("rejects a polygon outside the pilot area", () => {
    const outside: Ring = square.map(([lon, lat]) => [lon + 5, lat] as const);
    const report = validateFieldGeometry(outside, counties);
    expect(report.valid).toBe(false);
    expect(report.issues.map((i) => i.code)).toContain("outside_pilot_area");
    expect(report.county).toBeNull();
  });

  it("rejects non-finite coordinates", () => {
    const bad: Ring = [...square.slice(0, 3), [Number.NaN, 42], square[0]];
    expect(validateFieldGeometry(bad, counties).issues[0].code).toBe(
      "invalid_coordinate",
    );
  });
});

describe("geometry helpers", () => {
  it("computes the area of a 0.01° square within 1% of a hand calculation", () => {
    // 0.01° lon × cos(42.005°) × 111.195 km  ×  0.01° lat × 111.195 km
    const expectedHa =
      0.01 * Math.cos((42.005 * Math.PI) / 180) * 111.195 * 0.01 * 111.195 * 100;
    expect(Math.abs(ringAreaHa(square) - expectedHa) / expectedHa).toBeLessThan(0.01);
  });

  it("tests point-in-polygon on the square", () => {
    expect(pointInRing([-93.495, 42.005], square)).toBe(true);
    expect(pointInRing([-93.4, 42.005], square)).toBe(false);
  });
});

describe("demo field data (data/fields/fields.geojson)", () => {
  it("has 45 fields: one primary, the rest test, all labelled as demonstration polygons", () => {
    expect(demoFields).toHaveLength(45);
    expect(demoFields.filter((field) => field.role === "primary")).toHaveLength(1);
    expect(demoFields.every((field) => field.boundarySource === "demo")).toBe(true);
  });

  it("has unique field ids", () => {
    expect(new Set(demoFields.map((field) => field.id)).size).toBe(demoFields.length);
  });

  it.each(demoFields.map((field) => [field.id, field] as const))(
    "%s passes validation, sits in its stated county and matches its recorded area",
    (_id, field) => {
      const report = validateFieldGeometry(field.ring, counties);
      expect(report.issues).toEqual([]);
      expect(report.county).toBe(field.county);
      expect(Math.abs(report.areaHa! - field.areaHa) / field.areaHa).toBeLessThan(0.02);
    },
  );
});
