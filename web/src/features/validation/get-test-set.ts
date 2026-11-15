import { apiBaseUrl, callApi, ServiceError } from "@/lib/api";

/** One test field's row in the audit, as `GET /validation/test-set` returns it. */
export interface TestSetField {
  field_id: string;
  role: string | null;
  county: string | null;
  sequence_summary: string;
  expected_outcome: string;
  engine_outcome: string;
  match: boolean;
  scenarios: { scenario: string; outcome: string }[];
}

export interface TestSet {
  data_version: string;
  engine_version: string;
  run_id: string;
  headline_scenario: string;
  fields: TestSetField[];
  outcome_counts: Record<string, number>;
  match_count: number;
  /** Where the expected outcomes come from: DS1's handover, the selection label, or both. */
  expected_source: "ds1_expected" | "selection_label" | "mixed";
  expected_basis: string;
  cdl_agreement: {
    reference: string;
    metrics: {
      fields_compared: number;
      fields_agreeing: number;
      fields_disagreeing: number;
      disagreements: { selection_label: string; ds1_class: string; fields: number }[];
    };
    note: string;
  };
  caveats: string[];
}

export type TestSetResult =
  | { status: "available"; audit: TestSet }
  | { status: "no_service" } // AGROCYCLE_API_URL is not set
  | { status: "not_loaded" } // the service has no audit yet
  | { status: "unreachable" };

/**
 * The test-set audit, read from the API. This is a section of a page that is otherwise static, so a failing
 * service is reported on the page (`unreachable`) rather than taking the whole page down.
 */
export async function getTestSet(): Promise<TestSetResult> {
  const baseUrl = apiBaseUrl();
  if (!baseUrl) return { status: "no_service" };
  try {
    const body = await callApi(baseUrl, "/validation/test-set");
    return body
      ? { status: "available", audit: body as TestSet }
      : { status: "not_loaded" };
  } catch (error) {
    if (error instanceof ServiceError) {
      return { status: error.status === 503 ? "not_loaded" : "unreachable" };
    }
    throw error;
  }
}
