import { afterEach, describe, expect, it, vi } from "vitest";
import { ServiceError } from "@/lib/api";
import { fetchProfile } from "./api-client";
import { getFieldProfile } from "./get-field-profile";

const notLoaded = { status: "not_loaded", data: null, provenance: null };
const good = {
  fieldId: "primary-001",
  cropHistory: {
    status: "available",
    data: { years: [], summary: "x", repeatedYears: [] },
    provenance: null,
  },
  climate: notLoaded,
  vegetation: notLoaded,
  soil: notLoaded,
};

const reply = (status: number, body: unknown) =>
  vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("fetchProfile", () => {
  it("returns the API's profile and asks for the right path", async () => {
    const fetchMock = reply(200, good);
    vi.stubGlobal("fetch", fetchMock);
    const profile = await fetchProfile("http://api", "primary-001");
    expect(fetchMock.mock.calls[0][0]).toBe("http://api/fields/primary-001/profile");
    expect(fetchMock.mock.calls[0][1].method).toBe("GET");
    expect(profile?.climate.status).toBe("not_loaded");
  });

  it("returns undefined for a field the API does not know", async () => {
    vi.stubGlobal("fetch", reply(404, { detail: "no" }));
    expect(await fetchProfile("http://api", "nope")).toBeUndefined();
  });

  it.each([500, 503])("throws on status %i", async (status) => {
    vi.stubGlobal("fetch", reply(status, {}));
    await expect(fetchProfile("http://api", "primary-001")).rejects.toThrow(ServiceError);
  });

  it.each([
    ["not an object", "oops"],
    ["a missing section", { ...good, soil: undefined }],
    [
      "the frontend-only status 'sample'",
      { ...good, climate: { ...notLoaded, status: "sample" } },
    ],
    [
      "an available section with no data",
      { ...good, cropHistory: { ...notLoaded, status: "available" } },
    ],
    ["no field id", { ...good, fieldId: undefined }],
  ])("rejects a response with %s", async (_label, body) => {
    vi.stubGlobal("fetch", reply(200, body));
    await expect(fetchProfile("http://api", "primary-001")).rejects.toThrow(
      /unexpected answer/,
    );
  });
});

describe("getFieldProfile", () => {
  it("builds the labelled-sample profile locally when no API is configured", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const profile = await getFieldProfile("primary-001");
    expect(profile?.climate.status).toBe("sample");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("uses the API, and shows what it says, when AGROCYCLE_API_URL is set", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", reply(200, good));
    const profile = await getFieldProfile("primary-001");
    expect(profile?.climate.status).toBe("not_loaded");
  });

  it("returns undefined for a field the service says it does not have", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", reply(404, {}));
    expect(await getFieldProfile("nope")).toBeUndefined();
  });

  it("lets a failing API surface instead of showing sample data in its place", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", reply(500, {}));
    await expect(getFieldProfile("primary-001")).rejects.toThrow(ServiceError);
  });
});
