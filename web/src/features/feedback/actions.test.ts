import { afterEach, describe, expect, it, vi } from "vitest";
import { sendFeedback } from "./actions";
import { emptyDraft, type FeedbackDraft } from "./payload";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

const draft: FeedbackDraft = {
  ...emptyDraft("primary-001"),
  role: "adviser",
  usefulness: 5,
  clarity: 4,
};
const respond = (status: number, body: unknown = {}) =>
  vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));

describe("sendFeedback", () => {
  it("does not call the service for a form that is not valid", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    expect(await sendFeedback({ ...draft, role: "" })).toMatchObject({ ok: false });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("says it cannot take feedback, and sends nothing, when no service is configured", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    expect(await sendFeedback(draft)).toMatchObject({
      ok: false,
      message: expect.stringMatching(/not connected/),
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("posts the request and returns the thanks and the Iowa note", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    const fetchMock = respond(200, {
      message: "Thank you.",
      iowa_note: "Not Iowa agronomy.",
    });
    vi.stubGlobal("fetch", fetchMock);
    expect(await sendFeedback(draft)).toEqual({
      ok: true,
      message: "Thank you.",
      iowaNote: "Not Iowa agronomy.",
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api/api/v1/feedback");
    expect(JSON.parse(init.body)).toMatchObject({
      role: "adviser",
      usefulness: 5,
      field_id: "primary-001",
    });
  });

  it("explains a rate limit, a rejected form and an unreachable service", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal("fetch", respond(429));
    expect(await sendFeedback(draft)).toMatchObject({
      ok: false,
      message: expect.stringMatching(/a lot of feedback/i),
    });
    vi.stubGlobal("fetch", respond(422));
    expect(await sendFeedback(draft)).toMatchObject({
      ok: false,
      message: expect.stringMatching(/could not be accepted/),
    });
    vi.stubGlobal("fetch", respond(500));
    expect(await sendFeedback(draft)).toMatchObject({
      ok: false,
      message: expect.stringMatching(/could not be reached/),
    });
  });
});
