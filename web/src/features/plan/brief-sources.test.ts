import { describe, expect, it } from "vitest";
import { getComparison } from "@/features/compare/get-comparison";
import { cropHistoryPeriod, profileSources } from "./brief-sources";

describe("brief sources", () => {
  it("gives the crop-history period and lists the crop and soil sources", async () => {
    const { profile } = (await getComparison("primary-001", {}, { preview: false }))!;
    expect(cropHistoryPeriod(profile)).toBe("2015 to 2025");
    const uses = profileSources(profile).map((s) => s.use);
    expect(uses).toContain("Crop history");
    expect(uses).toContain("Soil");
  });

  it("does not list sample values as a source", async () => {
    const { profile } = (await getComparison("primary-001", {}, { preview: false }))!;
    expect(profile?.climate.status).toBe("sample");
    const sources = profileSources(profile).map((s) => s.source);
    expect(sources).not.toContain("NASA POWER");
  });

  it("says nothing when there is no profile", () => {
    expect(profileSources(undefined)).toEqual([]);
    expect(cropHistoryPeriod(undefined)).toBeUndefined();
  });
});
