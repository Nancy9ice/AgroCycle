import { describe, expect, it } from "vitest";
import {
  MAX_FILE_VERTICES,
  centreOf,
  parseBoundaryFile,
  zoomFor,
  type BoundaryFileResult,
} from "./boundary-file";

const ring = [
  [-93.5, 42.0],
  [-93.49, 42.0],
  [-93.49, 42.01],
  [-93.5, 42.01],
  [-93.5, 42.0],
];
const polygon = { type: "Polygon", coordinates: [ring] };
const file = (value: unknown) => JSON.stringify(value);
const message = (result: BoundaryFileResult) => (result.ok ? "" : result.message);

describe("parseBoundaryFile: what it accepts", () => {
  const expected = ring.slice(0, -1);

  it.each([
    ["a Polygon", polygon],
    ["a Feature", { type: "Feature", properties: {}, geometry: polygon }],
    [
      "a one-feature collection",
      { type: "FeatureCollection", features: [{ type: "Feature", geometry: polygon }] },
    ],
    ["a one-polygon MultiPolygon", { type: "MultiPolygon", coordinates: [[ring]] }],
  ])("reads %s and drops the closing point", (_name, value) => {
    expect(parseBoundaryFile(file(value))).toEqual({ ok: true, corners: expected });
  });

  it("accepts a ring that is not closed, and a position with a height", () => {
    const open = {
      type: "Polygon",
      coordinates: [ring.slice(0, -1).map(([x, y]) => [x, y, 300])],
    };
    expect(parseBoundaryFile(file(open))).toEqual({ ok: true, corners: expected });
  });

  it("accepts a file that names WGS 84 as its coordinate system", () => {
    const named = {
      ...polygon,
      crs: { type: "name", properties: { name: "urn:ogc:def:crs:OGC:1.3:CRS84" } },
    };
    expect(parseBoundaryFile(file(named)).ok).toBe(true);
  });
});

describe("parseBoundaryFile: what it refuses, and why", () => {
  it("says a file that is not JSON could not be read", () => {
    expect(message(parseBoundaryFile("not json at all"))).toMatch(
      /could not be read as GeoJSON/,
    );
  });

  it("refuses more than one field, in a collection or a MultiPolygon", () => {
    const two = {
      type: "FeatureCollection",
      features: [
        { type: "Feature", geometry: polygon },
        { type: "Feature", geometry: polygon },
      ],
    };
    expect(message(parseBoundaryFile(file(two)))).toMatch(/2 shapes.*one field per file/);
    expect(
      message(
        parseBoundaryFile(file({ type: "MultiPolygon", coordinates: [[ring], [ring]] })),
      ),
    ).toMatch(/2 separate areas/);
  });

  it("refuses a boundary with a hole rather than quietly using only the outside", () => {
    expect(
      message(parseBoundaryFile(file({ type: "Polygon", coordinates: [ring, ring] }))),
    ).toMatch(/hole/);
  });

  it("refuses shapes that are not polygons", () => {
    expect(
      message(parseBoundaryFile(file({ type: "Point", coordinates: [-93.5, 42] }))),
    ).toMatch(/must be a polygon.*Point/);
    expect(
      message(parseBoundaryFile(file({ type: "LineString", coordinates: ring }))),
    ).toMatch(/LineString/);
  });

  it("refuses an empty collection and a feature with no boundary", () => {
    expect(
      message(parseBoundaryFile(file({ type: "FeatureCollection", features: [] }))),
    ).toMatch(/no shapes/);
    expect(message(parseBoundaryFile(file({ type: "Feature", geometry: null })))).toMatch(
      /no boundary/,
    );
  });

  it("recognises projected coordinates (metres) and a different coordinate system", () => {
    const utm = {
      type: "Polygon",
      coordinates: [
        [
          [450000, 4650000],
          [450100, 4650000],
          [450100, 4650100],
          [450000, 4650000],
        ],
      ],
    };
    expect(message(parseBoundaryFile(file(utm)))).toMatch(/look like metres/);
    const other = {
      ...polygon,
      crs: { type: "name", properties: { name: "EPSG:32615" } },
    };
    expect(message(parseBoundaryFile(file(other)))).toMatch(/other than WGS 84/);
  });

  it("refuses non-numeric points and too few corners", () => {
    expect(
      message(
        parseBoundaryFile(
          file({
            type: "Polygon",
            coordinates: [
              [
                [-93.5, "x"],
                [1, 1],
                [2, 2],
                [-93.5, "x"],
              ],
            ],
          }),
        ),
      ),
    ).toMatch(/not valid numbers/);
    expect(
      message(
        parseBoundaryFile(
          file({
            type: "Polygon",
            coordinates: [
              [
                [0, 0],
                [1, 1],
                [0, 0],
              ],
            ],
          }),
        ),
      ),
    ).toMatch(/at least three corners/);
  });

  it("refuses more points than the API accepts", () => {
    const many = Array.from({ length: MAX_FILE_VERTICES + 1 }, (_, i) => [
      -93.5 + i * 1e-6,
      42,
    ]);
    expect(
      message(parseBoundaryFile(file({ type: "Polygon", coordinates: [many] }))),
    ).toMatch(/limit is 2000/);
  });

  it("does not judge the boundary: a crossing or oversized one still reads, and the normal checks refuse it later", () => {
    const bowTie = {
      type: "Polygon",
      coordinates: [
        [
          [-93.5, 42],
          [-93.4, 42.1],
          [-93.4, 42],
          [-93.5, 42.1],
          [-93.5, 42],
        ],
      ],
    };
    expect(parseBoundaryFile(file(bowTie)).ok).toBe(true);
  });
});

describe("map framing", () => {
  const corners = ring.slice(0, -1) as [number, number][];

  it("centres on the boundary", () => {
    const [lon, lat] = centreOf(corners);
    expect(lon).toBeCloseTo(-93.495, 9);
    expect(lat).toBeCloseTo(42.005, 9);
  });

  it("zooms closer for a small field and further out for a large one", () => {
    const big = corners
      .map(([x, y]) => [x * 1, y * 1] as [number, number])
      .map(([x, y], i) =>
        i === 2 ? ([x + 0.2, y + 0.2] as [number, number]) : ([x, y] as [number, number]),
      );
    expect(zoomFor(corners)).toBeGreaterThan(zoomFor(big));
    expect(zoomFor(corners)).toBeGreaterThanOrEqual(13);
    expect(zoomFor(corners)).toBeLessThanOrEqual(17);
  });
});
