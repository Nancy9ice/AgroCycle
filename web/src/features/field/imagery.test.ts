import { describe, expect, it } from "vitest";
import { flightLabel, parseImagery } from "./imagery";

const good = {
  field_id: "primary-001",
  available: true,
  year: 2025,
  tiles: [{ tile_id: "ia_m_4209317_se_15_060_20250805", flight_date: "2025-08-05" }],
  resolution_m: 0.6,
  bounds: [-93.66, 42.0, -93.64, 42.02],
  evidence_type: "observed",
  attribution: "Aerial photo: USDA Farm Service Agency (NAIP)",
  note: "One aerial photo from one day, not a crop map.",
};

describe("parseImagery", () => {
  it("accepts the API's answer", () => {
    const parsed = parseImagery(good);
    expect(parsed?.bounds).toEqual([-93.66, 42.0, -93.64, 42.02]);
    expect(parsed?.tiles).toHaveLength(1);
  });

  it("treats 'no photo' as none", () => {
    expect(parseImagery({ field_id: "x", available: false })).toBeNull();
  });

  it("refuses bounds that would put the photo in the wrong place", () => {
    expect(parseImagery({ ...good, bounds: [-93.64, 42.0, -93.66, 42.02] })).toBeNull();
    expect(parseImagery({ ...good, bounds: [-93.66, 42.0, -93.64] })).toBeNull();
    expect(parseImagery({ ...good, bounds: [-993, 42.0, -93.64, 42.02] })).toBeNull();
    expect(parseImagery({ ...good, bounds: [-93.66, "42", -93.64, 42.02] })).toBeNull();
  });

  it("refuses an answer with no flight date, because the photo must say when it was taken", () => {
    expect(parseImagery({ ...good, tiles: [] })).toBeNull();
    expect(
      parseImagery({ ...good, tiles: [{ tile_id: "a", flight_date: "August" }] }),
    ).toBeNull();
  });

  it("refuses things that are not an object", () => {
    for (const value of [null, undefined, "x", 3, []])
      expect(parseImagery(value)).toBeNull();
  });
});

describe("flightLabel", () => {
  it("names one flight date", () => {
    expect(flightLabel([{ tile_id: "a", flight_date: "2025-08-05" }])).toBe(
      "5 August 2025",
    );
  });

  it("does not repeat a date for two tiles flown the same day", () => {
    expect(
      flightLabel([
        { tile_id: "a", flight_date: "2025-08-05" },
        { tile_id: "b", flight_date: "2025-08-05" },
      ]),
    ).toBe("5 August 2025");
  });

  it("names both dates when a field was cut from two flights", () => {
    expect(
      flightLabel([
        { tile_id: "b", flight_date: "2025-09-14" },
        { tile_id: "a", flight_date: "2025-08-05" },
      ]),
    ).toBe("5 August and 14 September 2025");
  });

  it("keeps the year on each date when the flights are in different years", () => {
    expect(
      flightLabel([
        { tile_id: "a", flight_date: "2023-08-05" },
        { tile_id: "b", flight_date: "2025-09-14" },
      ]),
    ).toBe("5 August 2023 and 14 September 2025");
  });
});
