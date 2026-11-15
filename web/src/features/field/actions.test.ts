import { afterEach, describe, expect, it, vi } from "vitest";
import { saveCropHistory, saveDrawnBoundary } from "./actions";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

const respond = (status: number, body: unknown = {}) =>
  vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));

const ring = [
  [-93.5, 42.0],
  [-93.49, 42.0],
  [-93.49, 42.01],
  [-93.5, 42.0],
] as const;

describe("saveDrawnBoundary", () => {
  it("says it cannot keep the boundary, and sends nothing, when no service is configured", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const result = await saveDrawnBoundary(ring);
    expect(result.ok).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("sends the boundary as a single polygon and returns the new id", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const fetchMock = respond(200, {
      valid: true,
      field_id: "drawn-ab12cd34",
      errors: [],
    });
    vi.stubGlobal("fetch", fetchMock);
    expect(await saveDrawnBoundary(ring)).toEqual({
      ok: true,
      fieldId: "drawn-ab12cd34",
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api/api/v1/fields/drawn");
    expect(JSON.parse(init.body)).toEqual({
      geometry: { type: "Polygon", coordinates: [ring] },
    });
  });

  it("passes on why the API refused a boundary", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal(
      "fetch",
      respond(200, { valid: false, field_id: "", errors: [{ message: "Too large." }] }),
    );
    expect(await saveDrawnBoundary(ring)).toEqual({ ok: false, message: "Too large." });
  });

  it("explains a rate limit and an unreachable service in plain words", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", respond(429));
    expect(await saveDrawnBoundary(ring)).toMatchObject({
      ok: false,
      message: expect.stringMatching(/Too many/),
    });
    vi.stubGlobal("fetch", respond(500));
    expect(await saveDrawnBoundary(ring)).toMatchObject({
      ok: false,
      message: expect.stringMatching(/could not be reached/),
    });
  });
});

describe("saveCropHistory", () => {
  const crops = Array(11).fill("corn");

  it("sends the farmer's crops and returns the class the rules gave", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const fetchMock = respond(200, {
      field_class: "continuous_corn",
      summary: "Corn in every year.",
    });
    vi.stubGlobal("fetch", fetchMock);
    expect(await saveCropHistory("drawn-ab12cd34", crops)).toEqual({
      ok: true,
      fieldClass: "continuous_corn",
      summary: "Corn in every year.",
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api/api/v1/fields/drawn-ab12cd34/crop-history");
    expect(JSON.parse(init.body)).toEqual({ crops });
  });

  it("reports a rejected answer and a field the API does not know", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", respond(422));
    expect(await saveCropHistory("drawn-ab12cd34", crops)).toMatchObject({
      ok: false,
      message: expect.stringMatching(/every season/),
    });
    vi.stubGlobal("fetch", respond(404));
    expect(await saveCropHistory("drawn-nothere", crops)).toMatchObject({
      ok: false,
      message: expect.stringMatching(/could not find/),
    });
  });
});
