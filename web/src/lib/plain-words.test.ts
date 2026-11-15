import { describe, expect, it } from "vitest";
import { plain } from "./plain-words";

describe("plain", () => {
  it("says corn, as an Iowa farmer does", () => {
    expect(plain("The two-year maize–soybean rotation")).toBe(
      "The two-year corn–soybean rotation",
    );
    expect(plain("Maize and soybean yields matched")).toBe(
      "Corn and soybean yields matched",
    );
  });

  it("never leaves an internal document reference on screen", () => {
    expect(plain("PRD section 7.4")).not.toMatch(/PRD/);
    expect(plain("PRD section 7.4 and 4.4")).not.toMatch(/PRD/);
    expect(plain("Davis et al. (2012); AgroCycle scope (PRD section 9)")).toBe(
      "Davis et al. (2012)",
    );
  });

  it("keeps the citation it does not need to change", () => {
    expect(plain("Davis et al. (2012), supplementary records")).toBe(
      "Davis et al. (2012), supplementary records",
    );
  });

  it("rewrites the engine sentences a farmer sees most", () => {
    expect(plain("One or more required profile indicators came back unknown.")).toMatch(
      /weather or soil measurements/,
    );
    expect(
      plain(
        "Every applicability rule is a team-proposed guardrail and is not expert-reviewed.",
      ),
    ).toMatch(/No expert has checked them yet/);
  });

  it("passes unknown text through unchanged", () => {
    const text = "A sentence a later engine version might add.";
    expect(plain(text)).toBe(text);
  });
});
