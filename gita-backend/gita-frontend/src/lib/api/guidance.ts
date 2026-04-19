import { getPublicApiBaseUrl } from "./config";
import { ApiError, apiJson } from "./client";
import { parseRetrieveGuidanceResponse } from "./adapters";
import type { RetrieveGuidanceResponse } from "@/types/guidance";

export async function postGuidanceRetrieve(
  query: string,
  signal?: AbortSignal,
): Promise<RetrieveGuidanceResponse> {
  const raw = await apiJson<unknown>("/api/v1/guidance/retrieve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
    signal,
  });
  return parseRetrieveGuidanceResponse(raw);
}

/** Raw fetch for SSE — caller reads `body` stream */
export async function postGuidanceStream(
  query: string,
  signal: AbortSignal,
): Promise<Response> {
  const base = getPublicApiBaseUrl();
  const url = `${base}/api/v1/guidance/stream`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ query }),
    signal,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(`Stream failed: HTTP ${res.status}`, res.status, text);
  }
  if (!res.body) {
    throw new ApiError("Stream failed: no response body", res.status, "");
  }
  return res;
}
