import { describe, expect, it, vi } from "vitest";
import { counties, demoFields } from "./data";
import {
  checkDraftBoundary,
  describeArea,
  findPosition,
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

describe("findPosition", () => {
  const found = {
    coords: { longitude: -93.5, latitude: 42.03, accuracy: 20 },
  } as GeolocationPosition;
  const failure = (code: number) => ({ code }) as GeolocationPositionError;

  /** A device that answers each ask with the next scripted outcome, and records the options it was given. */
  const device = (...outcomes: (GeolocationPosition | GeolocationPositionError)[]) => {
    const asked: PositionOptions[] = [];
    const geolocation = {
      getCurrentPosition: vi.fn(
        (
          ok: PositionCallback,
          bad?: PositionErrorCallback | null,
          options?: PositionOptions,
        ) => {
          asked.push(options ?? {});
          const next = outcomes.shift()!;
          if ("coords" in next) ok(next);
          else bad?.(next);
        },
      ),
    };
    return { geolocation, asked };
  };

  it("takes a precise position when the device gives one, and asks only once", () => {
    const { geolocation, asked } = device(found);
    const onFound = vi.fn();
    findPosition(geolocation, onFound, vi.fn());
    expect(onFound).toHaveBeenCalledWith(found);
    expect(asked).toHaveLength(1);
    expect(asked[0].enableHighAccuracy).toBe(true);
  });

  it.each([2, 3])(
    "falls back to a rough position when the precise ask fails with code %i",
    (code) => {
      const { geolocation, asked } = device(failure(code), found);
      const onFound = vi.fn();
      const onFailed = vi.fn();
      findPosition(geolocation, onFound, onFailed);
      expect(onFound).toHaveBeenCalledWith(found);
      expect(onFailed).not.toHaveBeenCalled();
      expect(asked.map((o) => o.enableHighAccuracy)).toEqual([true, false]);
    },
  );

  it("does not ask again after a refusal", () => {
    const { geolocation, asked } = device(failure(1));
    const onFailed = vi.fn();
    findPosition(geolocation, vi.fn(), onFailed);
    expect(onFailed).toHaveBeenCalledWith(expect.objectContaining({ code: 1 }));
    expect(asked).toHaveLength(1);
  });

  it("reports the failure when the rough ask fails too", () => {
    const { geolocation } = device(failure(2), failure(2));
    const onFailed = vi.fn();
    findPosition(geolocation, vi.fn(), onFailed);
    expect(onFailed).toHaveBeenCalledWith(expect.objectContaining({ code: 2 }));
  });
});
