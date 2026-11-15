"use server";

import { ServiceError, apiBaseUrl, callApi } from "@/lib/api";
import { problem, toRequest, type FeedbackDraft } from "./payload";

export type SendFeedbackResult =
  { ok: true; message: string; iowaNote: string } | { ok: false; message: string };

/** Sends the feedback form (`POST /feedback`). The API validates again and is the source of truth. */
export async function sendFeedback(draft: FeedbackDraft): Promise<SendFeedbackResult> {
  const invalid = problem(draft);
  if (invalid) return { ok: false, message: invalid };

  const baseUrl = apiBaseUrl();
  if (!baseUrl) {
    return {
      ok: false,
      message:
        "This copy of the site is not connected to the data service, so it cannot take feedback.",
    };
  }
  try {
    const body = (await callApi(baseUrl, "/feedback", {
      method: "POST",
      body: toRequest(draft),
    })) as { message: string; iowa_note: string } | undefined;
    if (!body)
      return {
        ok: false,
        message: "The service could not take your feedback. Try again.",
      };
    return { ok: true, message: body.message, iowaNote: body.iowa_note };
  } catch (error) {
    if (error instanceof ServiceError) {
      if (error.status === 429) {
        return {
          ok: false,
          message:
            "A lot of feedback arrived just now. Please try again in a little while.",
        };
      }
      if (error.status === 422) {
        return {
          ok: false,
          message: "Some answers could not be accepted. Check the form and try again.",
        };
      }
    }
    return {
      ok: false,
      message: "The data service could not be reached. Try again in a moment.",
    };
  }
}
