import { NextResponse } from "next/server";
import { ServiceError, apiBaseUrl, callApi } from "@/lib/api";

/**
 * What aerial photo there is for a field, from the API. The browser asks this route, not the API, because
 * the API's address is private to the server (see `lib/api.ts`). With no API configured there are no
 * photos, and nothing is made up.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ fieldId: string }> },
) {
  const { fieldId } = await params;
  const baseUrl = apiBaseUrl();
  if (!baseUrl) return NextResponse.json({ available: false });
  try {
    const body = await callApi(baseUrl, `/fields/${encodeURIComponent(fieldId)}/imagery`);
    return NextResponse.json(body ?? { available: false });
  } catch (error) {
    const message =
      error instanceof ServiceError ? error.message : "Something went wrong.";
    return NextResponse.json({ available: false, error: message }, { status: 502 });
  }
}
