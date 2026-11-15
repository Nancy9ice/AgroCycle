import { afterEach, describe, expect, it, vi } from "vitest";
import { getTestSet } from "./get-test-set";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

const respond = (status: number, body: unknown = {}) =>
  vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));

describe("getTestSet", () => {
  it("says there is no service, and calls nothing, when none is configured", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    expect(await getTestSet()).toEqual({ status: "no_service" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("returns the audit the service sends", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const audit = { fields: [], outcome_counts: { abstention: 18 } };
    const fetchMock = respond(200, audit);
    vi.stubGlobal("fetch", fetchMock);
    expect(await getTestSet()).toEqual({ status: "available", audit });
    expect(fetchMock.mock.calls[0][0]).toBe("http://api/api/v1/validation/test-set");
  });

  it("tells 'not loaded yet' (503) from 'unreachable'", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", respond(503));
    expect(await getTestSet()).toEqual({ status: "not_loaded" });
    vi.stubGlobal("fetch", respond(500));
    expect(await getTestSet()).toEqual({ status: "unreachable" });
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("down")));
    expect(await getTestSet()).toEqual({ status: "unreachable" });
  });
});
