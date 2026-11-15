import { describe, expect, it } from "vitest";
import { counties, demoFields } from "./data";
import {
  checkDraftBoundary,
  describeArea,
  locateInPilot,
  locationErrorMessage,
  ringFromCorners,
} from "./boundary-draft";
import type { LonLat } from "./types";

const primary = demoFields.find((field) => field.id === "primary-001")!;
// The demo field's own corners, without the closing point, as a farmer would tap them.
const primaryCorners = primary.ring.slice(0, -1);

describe("ringFromCorners", () => {
  it("gives nothing until there are three corners", () => {
    expect(ringFromCorners([])).toEqual([]);
    expect(
      ringFromCorners([
        [-93.6, 42.0],
        [-93.5, 42.0],
      ]),
    ).toEqual([]);
  });

  it("closes the ring by repeating the first corner", () => {
    const ring = ringFromCorners(primaryCorners);
    expect(ring).toHaveLength(primaryCorners.length + 1);
    expect(ring[ring.length - 1]).toEqual(ring[0]);
  });
});

describe("checkDraftBoundary", () => {
  it("accepts the corners of a real demo boundary", () => {
    const report = checkDraftBoundary(primaryCorners, counties);
    expect(report.valid).toBe(true);
    expect(report.county).toBe(primary.county);
  });

  it("says a boundary needs three corners", () => {
    const report = checkDraftBoundary(primaryCorners.slice(0, 2), counties);
    expect(report.valid).toBe(false);
    expect(report.issues[0].code).toBe("too_few_points");
  });

  it("rejects a boundary that crosses itself", () => {
    const [a, b, c, d] = primaryCorners.slice(0, 4);
    const bowtie: LonLat[] = [a, c, b, d];
    const report = checkDraftBoundary(bowtie, counties);
    expect(report.issues.map((issue) => issue.code)).toContain("self_intersection");
  });

  it("rejects a boundary outside Story and Boone", () => {
    const outside: LonLat[] = [
      [-91.5, 41.9],
      [-91.49, 41.9],
      [-91.49, 41.91],
    ];
    const report = checkDraftBoundary(outside, counties);
    expect(report.valid).toBe(false);
    expect(report.issues.map((issue) => issue.code)).toContain("outside_pilot_area");
  });
});

describe("describeArea", () => {
  it("leads with acres and keeps hectares for the adviser", () => {
    expect(describeArea(10)).toBe("25 acres (10 ha)");
    expect(describeArea(2)).toBe("4.9 acres (2.0 ha)");
  });
});

describe("locateInPilot", () => {
  it("places a position inside a pilot county", () => {
    const result = locateInPilot(primary.centroid, 20, counties);
    expect(result).toEqual({
      kind: "inside",
      county: primary.county,
      approximate: false,
    });
  });

  it("flags a rough position as approximate", () => {
    const result = locateInPilot(primary.centroid, 3000, counties);
    expect(result.kind === "inside" && result.approximate).toBe(true);
  });

  it("says outside for a position elsewhere in Iowa", () => {
    expect(locateInPilot([-91.5, 41.9], 20, counties)).toEqual({ kind: "outside" });
  });
});

describe("locationErrorMessage", () => {
  it("tells the farmer what to do next in each case", () => {
    for (const code of [1, 2, 3, "unsupported"] as const) {
      expect(locationErrorMessage(code)).toMatch(/map/);
    }
    expect(locationErrorMessage(1)).toMatch(/browser settings/);
  });
});
