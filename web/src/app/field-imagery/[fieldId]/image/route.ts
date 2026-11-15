import { apiBaseUrl } from "@/lib/api";

/** The aerial photo itself, passed through from the API unchanged. */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ fieldId: string }> },
) {
  const { fieldId } = await params;
  const baseUrl = apiBaseUrl();
  if (!baseUrl) return new Response("No aerial photos are configured.", { status: 404 });
  let upstream: Response;
  try {
    upstream = await fetch(
      `${baseUrl}/fields/${encodeURIComponent(fieldId)}/imagery/image.png`,
      {
        signal: AbortSignal.timeout(20_000),
      },
    );
  } catch {
    return new Response("The service could not be reached.", { status: 502 });
  }
  if (!upstream.ok || upstream.headers.get("content-type") !== "image/png") {
    return new Response("No aerial photo for this field.", {
      status: upstream.status === 404 ? 404 : 502,
    });
  }
  return new Response(upstream.body, {
    headers: {
      "content-type": "image/png",
      "cache-control": "public, max-age=3600",
    },
  });
}
