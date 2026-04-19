/**
 * Narrow unknown JSON into our domain types.
 * If backend fields change, update this file only.
 */

import type {
  GuidanceStreamEnvelope,
  GuidanceStreamEventName,
  RetrieveGuidanceResponse,
  StreamErrorPayload,
  StreamMetadataPayload,
  StreamTokenPayload,
  StreamVerseCard,
  StreamVersesPayload,
} from "@/types/guidance";

const STREAM_EVENTS: ReadonlySet<GuidanceStreamEventName> = new Set([
  "metadata",
  "verses",
  "token",
  "error",
  "completed",
]);

export function parseRetrieveGuidanceResponse(raw: unknown): RetrieveGuidanceResponse {
  if (!raw || typeof raw !== "object") {
    throw new Error("Retrieve response: expected object");
  }
  const o = raw as Record<string, unknown>;
  if (typeof o.query !== "string") throw new Error("Retrieve response: missing query");
  if (!Array.isArray(o.selected_verses)) throw new Error("Retrieve response: missing selected_verses");
  if (o.explanation_status !== "verses_only" && o.explanation_status !== "no_hits") {
    throw new Error("Retrieve response: invalid explanation_status");
  }
  return raw as RetrieveGuidanceResponse;
}

export function parseStreamEnvelope(line: string): GuidanceStreamEnvelope | null {
  const trimmed = line.trim();
  if (!trimmed.startsWith("data:")) return null;
  const payload = trimmed.slice(5).trim();
  if (!payload || payload === "[DONE]") return null;
  let obj: unknown;
  try {
    obj = JSON.parse(payload) as unknown;
  } catch {
    return null;
  }
  if (!obj || typeof obj !== "object") return null;
  const rec = obj as Record<string, unknown>;
  const event = rec.event;
  if (typeof event !== "string" || !STREAM_EVENTS.has(event as GuidanceStreamEventName)) {
    return null;
  }
  const data = rec.data;
  if (!data || typeof data !== "object") return null;
  return {
    event: event as GuidanceStreamEventName,
    data: data as Record<string, unknown>,
  };
}

export function asMetadataPayload(data: Record<string, unknown>): StreamMetadataPayload | null {
  if (typeof data.query !== "string") return null;
  if (typeof data.ollama_model !== "string") return null;
  if (typeof data.verse_count !== "number") return null;
  return data as unknown as StreamMetadataPayload;
}

export function asVersesPayload(data: Record<string, unknown>): StreamVersesPayload | null {
  const v = data.verses;
  if (!Array.isArray(v)) return null;
  return { verses: v as StreamVerseCard[] };
}

export function asTokenPayload(data: Record<string, unknown>): StreamTokenPayload | null {
  if (typeof data.text !== "string") return null;
  return { text: data.text };
}

export function asErrorPayload(data: Record<string, unknown>): StreamErrorPayload | null {
  if (typeof data.code !== "string" || typeof data.message !== "string") return null;
  return {
    code: data.code,
    message: data.message,
    fallback_used: typeof data.fallback_used === "boolean" ? data.fallback_used : undefined,
  };
}
