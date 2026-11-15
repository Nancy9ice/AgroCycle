import { afterEach, describe, expect, it, vi } from "vitest";
import { readApi } from "./api-read";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

const respond = (status: number, body: unknown = {}) =>
  vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));

describe("readApi", () => {
  it("reports no service, and calls nothing, when none is configured", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    expect(await readApi("/sources")).toEqual({ status: "no_service" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("returns the data, and tells 404, 503 and a failure apart", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", respond(200, [1]));
    expect(await readApi("/sources")).toEqual({ status: "ok", data: [1] });
    vi.stubGlobal("fetch", respond(404));
    expect(await readApi("/lineage/x")).toEqual({ status: "not_found" });
    vi.stubGlobal("fetch", respond(503));
    expect(await readApi("/sources")).toEqual({ status: "not_loaded" });
    vi.stubGlobal("fetch", respond(500));
    expect(await readApi("/sources")).toEqual({ status: "unreachable" });
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("down")));
    expect(await readApi("/sources")).toEqual({ status: "unreachable" });
  });
});
