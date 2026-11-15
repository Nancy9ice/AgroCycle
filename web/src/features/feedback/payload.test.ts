import { describe, expect, it } from "vitest";
import { emptyDraft, problem, toRequest, type FeedbackDraft } from "./payload";

const valid = (overrides: Partial<FeedbackDraft> = {}): FeedbackDraft => ({
  ...emptyDraft("primary-001", "a_123abc"),
  role: "farmer",
  usefulness: 4,
  clarity: 5,
  ...overrides,
});

describe("problem", () => {
  it("is null for the smallest valid form", () => {
    expect(problem(valid())).toBeNull();
  });

  it("asks for the three required answers, one at a time, in plain words", () => {
    expect(problem(valid({ role: "" }))).toMatch(/who you are/);
    expect(problem(valid({ usefulness: null }))).toMatch(/useful/);
    expect(problem(valid({ clarity: null }))).toMatch(/clear/);
  });

  it("refuses contact details without consent, rather than quietly dropping them", () => {
    expect(problem(valid({ contact: "me@example.com", consent: false }))).toMatch(
      /Tick the box/,
    );
    expect(problem(valid({ contact: "me@example.com", consent: true }))).toBeNull();
    expect(problem(valid({ contact: "   ", consent: false }))).toBeNull(); // blank is not a contact
  });

  it("stops text over the limit", () => {
    expect(problem(valid({ whatWasMissing: "x".repeat(1001) }))).toMatch(/1000/);
    expect(problem(valid({ whatWasMissing: "x".repeat(1000) }))).toBeNull();
  });
});

describe("toRequest", () => {
  it("sends a skipped answer as null, which means not provided, never as no or empty", () => {
    const body = toRequest(valid());
    expect(body).toMatchObject({
      role: "farmer",
      usefulness: 4,
      clarity: 5,
      farming_context: null,
      what_was_missing: null,
      would_use: null,
      contact: null,
      contact_consent: false,
      field_id: "primary-001",
      analysis_id: "a_123abc",
    });
  });

  it("trims text and keeps what was answered", () => {
    const body = toRequest(
      valid({
        farmingContext: "  Nigerian farmer  ",
        whatWasMissing: " a clearer map ",
        wouldUse: "maybe",
      }),
    );
    expect(body).toMatchObject({
      farming_context: "Nigerian farmer",
      what_was_missing: "a clearer map",
      would_use: "maybe",
    });
  });

  it("only records consent when there is a contact to keep", () => {
    expect(toRequest(valid({ consent: true })).contact_consent).toBe(false);
    expect(toRequest(valid({ contact: "me@example.com", consent: true }))).toMatchObject({
      contact: "me@example.com",
      contact_consent: true,
    });
  });

  it("does not link feedback to a field or comparison when there is none", () => {
    expect(
      toRequest({ ...emptyDraft(), role: "farmer", usefulness: 3, clarity: 3 }),
    ).toMatchObject({
      field_id: null,
      analysis_id: null,
    });
  });
});
