import { describe, expect, it } from "vitest";
import { demoFields } from "@/features/field/data";
import { buildCropHistory, parseCropSequence } from "./build-crop-history";
import { getFieldProfile } from "./get-field-profile";

describe("parseCropSequence", () => {
  it("gives one entry per year starting at the first year", () => {
    expect(parseCropSequence("CS", 2015)).toEqual([
      { year: 2015, code: "C" },
      { year: 2016, code: "S" },
    ]);
  });

  it("rejects an unknown crop code", () => {
    expect(() => parseCropSequence("CZ", 2015)).toThrow(/Unknown crop code/);
  });
});

describe("buildCropHistory summary", () => {
  it("describes a clean corn and soybean alternation", () => {
    const history = buildCropHistory("SCSCSCSCSCS", 2015);
    expect(history.summary).toMatch(/alternate every year, 2015 to 2025/);
    expect(history.repeatedYears).toEqual([]);
  });

  it("names the year a crop repeats in a mostly alternating sequence", () => {
    const history = buildCropHistory("SCCSCSCSCSC", 2015);
    expect(history.repeatedYears).toEqual([2017]);
    expect(history.summary).toMatch(/mostly alternating/);
    expect(history.summary).toMatch(/one year: corn in 2017/);
  });

  it("names several repeated years", () => {
    const history = buildCropHistory("CSCSSCSCCSC", 2015);
    expect(history.repeatedYears).toEqual([2019, 2023]);
    expect(history.summary).toMatch(/2 years: soybean in 2019 and corn in 2023/);
  });

  it("does not call a corn-heavy history alternating", () => {
    const history = buildCropHistory("CCCSCCSCCSC", 2015);
    expect(history.summary).not.toMatch(/alternat/);
  });

  it("describes a single crop in every year", () => {
    expect(buildCropHistory("GGGGGGGGGGG", 2015).summary).toBe(
      "Grass or pasture in every year, 2015 to 2025.",
    );
  });

  it("describes a mix, most frequent crop first", () => {
    const history = buildCropHistory("CCCSCCSCCSC", 2015);
    expect(history.summary).toBe(
      "A mix of crops, 2015 to 2025: corn 8 years, soybean 3 years.",
    );
  });
});

describe("demo field profiles (all 45 fields)", () => {
  it.each(demoFields.map((field) => [field.id, field] as const))(
    "%s has 11 years of crop history, soil from the data files, and labelled sample sections",
    async (id, field) => {
      const profile = await getFieldProfile(id);
      expect(profile).toBeDefined();
      expect(profile!.cropHistory.data!.years).toHaveLength(11);
      expect(profile!.cropHistory.data!.years[0].year).toBe(2015);
      expect(profile!.cropHistory.data!.years[10].year).toBe(2025);
      expect(profile!.cropHistory.status).toBe("available");
      expect(profile!.soil.status).toBe("available");
      expect(profile!.soil.data!.series.length).toBeGreaterThan(0);
      expect(profile!.climate.status).toBe("sample");
      expect(profile!.vegetation.status).toBe("sample");

      // The history agrees with the field's class from the field list.
      const codes = new Set(profile!.cropHistory.data!.years.map((y) => y.code));
      if (field.fieldClass === "rotation") expect([...codes].sort()).toEqual(["C", "S"]);
      if (field.fieldClass === "pasture") expect(codes.has("C")).toBe(false);
    },
  );

  it("returns undefined for an unknown field", async () => {
    expect(await getFieldProfile("nope")).toBeUndefined();
  });

  it("marks months with too few clear images as unknown, with no greenness value", async () => {
    const vegetation = (await getFieldProfile("primary-001"))!.vegetation.data!;
    for (const month of vegetation.months.filter((m) => m.state === "unknown")) {
      expect(month.ndvi).toBeNull();
    }
    expect(vegetation.months).toHaveLength(12);
  });
});
