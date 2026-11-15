import { apiBaseUrl, callApi, ServiceError } from "@/lib/api";

/** One test field's row in the audit, as `GET /validation/test-set` returns it. */
export interface TestSetField {
  field_id: string;
  role: string | null;
  county: string | null;
  sequence_summary: string;
  /** Written by DS2 from the validation matrix, for the headline scenario. Null for most fields, on purpose. */
  expected_outcome: string | null;
  expected_review_state: string | null;
  engine_outcome: string;
  /** Null when there is no expectation to compare with: that is not a failure. */
  match: boolean | null;
  scenarios: {
    scenario: string;
    outcome: string;
    expected_outcome: string | null;
    expected_review_state: string | null;
    match: boolean | null;
  }[];
}

export interface ExpectationSummary {
  cases_total: number;
  cases_with_expectation: number;
  cases_matching: number;
  fields_with_expectation: number;
  awaiting_review: number;
  reviewed: number;
  note: string;
}

export interface TestSet {
  data_version: string;
  engine_version: string;
  run_id: string;
  headline_scenario: string;
  fields: TestSetField[];
  outcome_counts: Record<string, number>;
  expectations: ExpectationSummary;
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
