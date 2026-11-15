import { afterEach, describe, expect, it, vi } from "vitest";
import { ServiceError } from "@/lib/api";
import { fetchDecision } from "./api-client";
import { getComparison } from "./get-comparison";
import { getSavedComparison } from "./get-saved-comparison";
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
  vi.fn().mockImplementation(async () => new Response(JSON.stringify(body), { status }));

/** A fake service that answers by URL, so a test sees every call the code makes. */
const service = (routes: Record<string, { status?: number; body: unknown }>) =>
  vi.fn(async (...[url]: [string, RequestInit?]) => {
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
  it("uses the offline copy when no API is configured, and says so", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const result = await getComparison("primary-001", {}, { preview: false });
    expect(result?.decision.outcome).toBe("abstention");
    expect(result?.provenance.source).toBe("offline_fallback");
    expect(result?.provenance.dataVersion).toBeUndefined();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("asks the API when AGROCYCLE_API_URL is set, and shows what the API said", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api/");
    const fetchMock = service({
      "/fields/demo": { body: [apiField] },
      "/meta/pilot-area": { body: apiArea },
      "/fields/primary-001/compare": {
        body: {
          ...goodBody,
          preview: true,
          analysis_id: "a_1",
          created_at: "2026-11-15T10:00:00+00:00",
          data_version: "dv-7",
        },
      },
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
    expect(result?.provenance).toEqual({
      source: "api",
      rulesVersion: goodBody.decision.rules_version,
      dataVersion: "dv-7",
      createdAt: "2026-11-15T10:00:00+00:00",
    });
  });

  it("takes the decision from the API, not from the web app's own copy of the engine", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    // A decision the local engine would never produce for this field and these answers.
    const marker = { ...goodBody.decision, outcome_reason: "the API decided this" };
    vi.stubGlobal(
      "fetch",
      service({
        "/fields/demo": { body: [apiField] },
        "/meta/pilot-area": { body: apiArea },
        "/fields/primary-001/compare": { body: { ...goodBody, decision: marker } },
      }),
    );
    const result = await getComparison("primary-001", {}, { preview: false });
    expect(result?.decision.outcome_reason).toBe("the API decided this");
  });

  it("still returns the comparison when only the profile service fails", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal(
      "fetch",
      service({
        "/fields/demo": { body: [apiField] },
        "/meta/pilot-area": { body: apiArea },
        "/fields/primary-001/compare": { body: goodBody },
        "/profile": { status: 503, body: {} },
      }),
    );
    const result = await getComparison("primary-001", {}, { preview: false });
    expect(result?.provenance.source).toBe("api");
    expect(result?.profile).toBeUndefined();
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

  it("lets a failing API surface instead of falling back to the offline copy", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", reply(500, {}));
    await expect(getComparison("primary-001", {}, { preview: false })).rejects.toThrow(
      ServiceError,
    );
  });
});

describe("the offline engine in production", () => {
  it("refuses to answer when no API is configured and the deployment has not opted in", async () => {
    vi.stubEnv("NODE_ENV", "production");
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    await expect(getComparison("primary-001", {}, { preview: false })).rejects.toThrow(
      ServiceError,
    );
    expect(error).toHaveBeenCalled();
    error.mockRestore();
  });

  it("runs the offline copy, labelled, when the deployment opts in on purpose", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("AGROCYCLE_ALLOW_OFFLINE_ENGINE", "true");
    const result = await getComparison("primary-001", {}, { preview: false });
    expect(result?.provenance.source).toBe("offline_fallback");
  });

  it("does not need the opt-in when the API is configured", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal(
      "fetch",
      service({
        "/fields/demo": { body: [apiField] },
        "/meta/pilot-area": { body: apiArea },
        "/fields/primary-001/compare": { body: goodBody },
      }),
    );
    const result = await getComparison("primary-001", {}, { preview: false });
    expect(result?.provenance.source).toBe("api");
  });
});

describe("context-only answers", () => {
  it("sends hay equipment, storage and labour to the API with the rest of the request", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const fetchMock = service({
      "/fields/demo": { body: [apiField] },
      "/meta/pilot-area": { body: apiArea },
      "/fields/primary-001/profile": { status: 404, body: {} },
      "/fields/primary-001/compare": {
        body: {
          ...goodBody,
          context_recorded: {
            hay_equipment_or_contractor: false,
            storage_space: null,
            extra_labour: "some",
          },
          context_note: "recorded, not used",
        },
      },
    });
    vi.stubGlobal("fetch", fetchMock);
    const result = await getComparison(
      "primary-001",
      { hayEquipment: "no", labour: "some" },
      { preview: false },
    );
    const call = fetchMock.mock.calls.find(([url]) => url.endsWith("/compare"));
    const sent = JSON.parse(String(call?.[1]?.body));
    expect(sent.context).toEqual({
      hay_equipment_or_contractor: false,
      storage_space: null,
      extra_labour: "some",
    });
    // What the API recorded is what the screen shows.
    expect(result?.context?.extra_labour).toBe("some");
    expect(result?.contextNote).toBe("recorded, not used");
  });
});

describe("getSavedComparison", () => {
  const stored = {
    ...goodBody,
    field: { field_id: "primary-001" },
    analysis_id: "a_123abc",
    created_at: "2026-11-15T12:00:00+00:00",
    data_version: "dv1",
    context_recorded: {
      hay_equipment_or_contractor: null,
      storage_space: false,
      extra_labour: null,
    },
  };

  it("has nothing to show when no API is configured", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    expect(await getSavedComparison("a_123abc")).toBeUndefined();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows the stored result as it was run, marked saved, without running it again", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const fetchMock = service({
      "/analyses/a_123abc": { body: stored },
      "/fields/demo": { body: [apiField] },
      "/meta/pilot-area": { body: apiArea },
    });
    vi.stubGlobal("fetch", fetchMock);
    const result = await getSavedComparison("a_123abc");
    expect(result?.saved).toBe(true);
    expect(result?.analysisId).toBe("a_123abc");
    expect(result?.provenance).toMatchObject({
      source: "api",
      dataVersion: "dv1",
      createdAt: "2026-11-15T12:00:00+00:00",
    });
    expect(result?.context?.storage_space).toBe(false);
    expect(fetchMock.mock.calls.some(([url]) => url.endsWith("/compare"))).toBe(false);
  });

  it("returns undefined for an unknown analysis, and for one whose field is not listed", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", service({}));
    expect(await getSavedComparison("nope")).toBeUndefined();
    vi.stubGlobal(
      "fetch",
      service({
        "/analyses/a_1": { body: { ...stored, field: { field_id: "gone" } } },
        "/fields/demo": { body: [apiField] },
        "/meta/pilot-area": { body: apiArea },
      }),
    );
    expect(await getSavedComparison("a_1")).toBeUndefined();
  });

  it("refuses an answer that is not a decision, and a failing service surfaces", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", service({ "/analyses/a_1": { body: { nope: true } } }));
    await expect(getSavedComparison("a_1")).rejects.toThrow(ServiceError);
    vi.stubGlobal("fetch", reply(500, {}));
    await expect(getSavedComparison("a_1")).rejects.toThrow(ServiceError);
  });
});

describe("priorities shape the comparison", () => {
  it("sends the farmer's levels, low included, and carries the emphasis back", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const emphasis = {
      outcome_order: ["nitrate_leaching_reduction"],
      highlighted: ["nitrate_leaching_reduction"],
      gaps_for_priorities: ["Nothing here measures water leaving your soil."],
      priorities_used: ["water"],
      note: "Your priorities decide what is shown first.",
    };
    const fetchMock = service({
      "/fields/demo": { body: [apiField] },
      "/meta/pilot-area": { body: apiArea },
      "/fields/primary-001/profile": { status: 404, body: {} },
      "/fields/primary-001/compare": { body: { ...goodBody, emphasis } },
    });
    vi.stubGlobal("fetch", fetchMock);
    const result = await getComparison(
      "primary-001",
      { water: "high", inputs: "low" },
      { preview: false },
    );
    const call = fetchMock.mock.calls.find(([url]) => url.endsWith("/compare"));
    expect(JSON.parse(String(call?.[1]?.body)).priority_levels).toEqual({
      water: "high",
      inputs: "low",
    });
    expect(result?.emphasis?.gaps_for_priorities[0]).toContain("water leaving your soil");
  });

  it("sends no priority levels when none were answered", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const fetchMock = service({
      "/fields/demo": { body: [apiField] },
      "/meta/pilot-area": { body: apiArea },
      "/fields/primary-001/profile": { status: 404, body: {} },
      "/fields/primary-001/compare": { body: goodBody },
    });
    vi.stubGlobal("fetch", fetchMock);
    await getComparison("primary-001", {}, { preview: false });
    const call = fetchMock.mock.calls.find(([url]) => url.endsWith("/compare"));
    expect("priority_levels" in JSON.parse(String(call?.[1]?.body))).toBe(false);
  });

  it("keeps the emphasis on a saved result, so a shared link shows the same gaps", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const emphasis = {
      outcome_order: [],
      highlighted: [],
      gaps_for_priorities: ["gap"],
      priorities_used: ["soil"],
      note: "n",
    };
    vi.stubGlobal(
      "fetch",
      service({
        "/analyses/a_1": {
          body: {
            ...goodBody,
            field: { field_id: "primary-001" },
            analysis_id: "a_1",
            emphasis,
          },
        },
        "/fields/demo": { body: [apiField] },
        "/meta/pilot-area": { body: apiArea },
      }),
    );
    expect((await getSavedComparison("a_1"))?.emphasis?.priorities_used).toEqual([
      "soil",
    ]);
  });
});
