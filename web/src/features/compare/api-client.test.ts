import { afterEach, describe, expect, it, vi } from "vitest";
import { ServiceError } from "@/lib/api";
import { fetchDecision } from "./api-client";
import { getComparison } from "./get-comparison";
import { assess } from "./evaluate";
import type { EngineConstraints, EngineProfile } from "./evaluate";

const constraints: EngineConstraints = {
  manure_access: false,
  forage_use_or_buyer: null,
  oat_use_or_buyer: true,
  small_grain_equipment_or_contractor: null,
  priorities: ["soil"],
};

const profile: EngineProfile = {
  field_id: "primary-001",
  boundary_source: "demo",
  crop_history_summary: "x",
  county: "Story",
  crop_history_is_maize_soybean: true,
  gdd_season_difference_vs_marsden: null,
  frost_free_days: null,
  dominant_drainage_class: null,
  indicator_statuses: {},
};
const goodBody = { decision: assess(profile, constraints), preview: false };

const reply = (status: number, body: unknown) =>
  vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));

/** A fake service that answers by URL, so a test sees every call the code makes. */
const service = (routes: Record<string, { status?: number; body: unknown }>) =>
  vi.fn(async (url: string) => {
    const hit = Object.entries(routes).find(([path]) => url.endsWith(path));
    const { status = 200, body } = hit?.[1] ?? { status: 404, body: {} };
    return new Response(JSON.stringify(body), { status });
  });

const apiField = {
  field_id: "primary-001",
  county: "Story",
  role: "primary",
  boundary_source: "demo",
  is_demo: true,
  area_ha: 43.5,
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [0, 0],
        [0, 1],
        [1, 1],
        [0, 0],
      ],
    ],
  },
  field_class: "rotation",
  domain_note: "in-domain: maize-soybean rotation",
  provenance: "demonstration geometry",
  cover_detail: null,
  centroid: [-93.48, 42.03],
};
const apiArea = {
  counties: [
    {
      county: "Story",
      ring: [
        [0, 0],
        [0, 1],
        [1, 1],
        [0, 0],
      ],
    },
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("fetchDecision", () => {
  it("sends only answers, priorities and the preview flag, with null kept as null", async () => {
    const fetchMock = reply(200, goodBody);
    vi.stubGlobal("fetch", fetchMock);
    await fetchDecision("http://api", "primary-001", constraints, true);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api/fields/primary-001/compare");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({
      manure_access: false,
      forage_use_or_buyer: null,
      oat_use_or_buyer: true,
      small_grain_equipment_or_contractor: null,
      priorities: ["soil"],
      sample_indicators: true,
    });
  });

  it("returns the decision and the preview flag from the API", async () => {
    vi.stubGlobal("fetch", reply(200, { ...goodBody, preview: true }));
    const result = await fetchDecision("http://api", "primary-001", constraints, true);
    expect(result?.preview).toBe(true);
    expect(result?.decision.outcome).toBe(goodBody.decision.outcome);
  });

  it("returns undefined when the API says the field does not exist", async () => {
    vi.stubGlobal("fetch", reply(404, { detail: "No field" }));
    expect(await fetchDecision("http://api", "nope", constraints, false)).toBeUndefined();
  });

  it.each([500, 422, 503])("throws, and does not guess, on status %i", async (status) => {
    vi.stubGlobal("fetch", reply(status, {}));
    await expect(
      fetchDecision("http://api", "primary-001", constraints, false),
    ).rejects.toThrow(ServiceError);
  });

  it("throws when the service cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));
    await expect(
      fetchDecision("http://api", "primary-001", constraints, false),
    ).rejects.toThrow(/could not be reached/);
  });

  it.each([
    ["not an object", "oops"],
    ["no decision", { preview: false }],
    [
      "an outcome the product does not allow",
      { preview: false, decision: { ...goodBody.decision, outcome: "recommended" } },
    ],
    [
      "missing outcomes",
      { preview: false, decision: { ...goodBody.decision, outcomes: undefined } },
    ],
  ])("rejects a response with %s", async (_label, body) => {
    vi.stubGlobal("fetch", reply(200, body));
    await expect(
      fetchDecision("http://api", "primary-001", constraints, false),
    ).rejects.toThrow(/unexpected answer/);
  });
});

describe("getComparison", () => {
  it("uses the local engine when no API is configured", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const result = await getComparison("primary-001", {}, { preview: false });
    expect(result?.decision.outcome).toBe("abstention");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("asks the API when AGROCYCLE_API_URL is set, and shows what the API said", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api/");
    const fetchMock = service({
      "/fields/demo": { body: [apiField] },
      "/meta/pilot-area": { body: apiArea },
      "/fields/primary-001/compare": { body: { ...goodBody, preview: true } },
    });
    vi.stubGlobal("fetch", fetchMock);
    const result = await getComparison(
      "primary-001",
      { manure: "no" },
      { preview: true },
    );
    const urls = fetchMock.mock.calls.map(([url]) => url);
    expect(urls).toContain("http://api/api/v1/fields/primary-001/compare");
    expect(result?.preview).toBe(true);
    // The field comes from the service, not from the web app's files.
    expect(result?.field.id).toBe("primary-001");
    expect(result?.field.provenance).toBe("demonstration geometry");
  });

  it("returns undefined for a field the service does not list, without running a comparison", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const fetchMock = service({
      "/fields/demo": { body: [apiField] },
      "/meta/pilot-area": { body: apiArea },
    });
    vi.stubGlobal("fetch", fetchMock);
    expect(await getComparison("nope", {}, { preview: false })).toBeUndefined();
    expect(fetchMock.mock.calls.some(([url]) => url.includes("/compare"))).toBe(false);
  });

  it("lets a failing API surface instead of falling back to the local engine", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", reply(500, {}));
    await expect(getComparison("primary-001", {}, { preview: false })).rejects.toThrow(
      ServiceError,
    );
  });
});
