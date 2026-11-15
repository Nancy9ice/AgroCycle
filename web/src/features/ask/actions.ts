"use server";

import { ServiceError, apiBaseUrl, callApi } from "@/lib/api";

export interface AskResult {
  refused: boolean;
  answer: string;
  citations: string[];
  error?: string;
}

async function ask(path: string, question: string, audience: string): Promise<AskResult> {
  const baseUrl = apiBaseUrl();
  if (!baseUrl) {
    return {
      refused: true,
      answer: "AI explanations are not available in this environment.",
      citations: [],
    };
  }
  try {
    const body = await callApi(baseUrl, path, {
      method: "POST",
      body: { question, audience },
    });
    if (body === undefined) {
      return {
        refused: true,
        answer: "Could not find the context to answer from.",
        citations: [],
      };
    }
    const r = body as { refused: boolean; answer: string; citations: string[] };
    return { refused: r.refused, answer: r.answer, citations: r.citations ?? [] };
  } catch (err) {
    const msg =
      err instanceof ServiceError ? err.message : "Something went wrong. Try again.";
    return { refused: true, answer: "", citations: [], error: msg };
  }
}

export async function askAnalysis(
  _prev: AskResult | null,
  formData: FormData,
): Promise<AskResult> {
  const analysisId = formData.get("contextId") as string;
  const question = (formData.get("question") as string).trim();
  const audience = (formData.get("audience") as string) || "farmer";
  if (!question)
    return { refused: true, answer: "Please enter a question.", citations: [] };
  return ask(`/analyses/${encodeURIComponent(analysisId)}/ask`, question, audience);
}

export async function askField(
  _prev: AskResult | null,
  formData: FormData,
): Promise<AskResult> {
  const fieldId = formData.get("contextId") as string;
  const question = (formData.get("question") as string).trim();
  const audience = (formData.get("audience") as string) || "farmer";
  if (!question)
    return { refused: true, answer: "Please enter a question.", citations: [] };
  return ask(`/fields/${encodeURIComponent(fieldId)}/ask`, question, audience);
}
