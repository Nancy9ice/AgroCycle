import { describe, expect, it } from "vitest";
import { choicesFromLetters, cropChoices, presets } from "./crop-choices";

describe("crop history form", () => {
  it("every quick start fills all 11 seasons with a crop the API accepts", () => {
    const allowed = new Set(cropChoices.map((c) => c.value));
    for (const preset of presets) {
      expect(preset.crops, preset.label).toHaveLength(11);
      expect(
        preset.crops.every((c) => allowed.has(c as never)),
        preset.label,
      ).toBe(true);
    }
  });

  it("the two rotation quick starts end on the crop they name", () => {
    expect(presets[0].crops[10]).toBe("corn");
    expect(presets[1].crops[10]).toBe("soybeans");
    expect(presets[0].crops.slice(0, 4)).toEqual([
      "corn",
      "soybeans",
      "corn",
      "soybeans",
    ]);
  });

  it("turns the profile's crop letters back into form values, so answers can be edited", () => {
    expect(choicesFromLetters(["C", "S", "O", "A", "G", "X"])).toEqual([
      "corn",
      "soybeans",
      "oats",
      "alfalfa",
      "pasture_hay",
      "other",
    ]);
    expect(choicesFromLetters(["L"])).toEqual([""]); // a letter the form cannot offer is left to choose again
  });
});
