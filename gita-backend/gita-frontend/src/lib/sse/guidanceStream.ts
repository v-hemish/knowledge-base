/**
 * Incremental SSE parser for POST /api/v1/guidance/stream.
 *
 * Backend sends frames as `data: <json>\\n\\n` where JSON matches
 * `{ event: string, data: object }` (see FastAPI `sse_data_line`).
 *
 * Safety:
 * - Ignore non-`data:` lines (comments, heartbeats).
 * - Skip malformed JSON or unknown `event` values (adapter returns null).
 * - Cap per-line length before JSON.parse to limit memory DoS from bad servers.
 */

import {
  parseStreamEnvelope,
  asMetadataPayload,
  asVersesPayload,
  asTokenPayload,
  asErrorPayload,
} from "@/lib/api/adapters";
import type { GuidanceStreamEnvelope } from "@/types/guidance";

const MAX_LINE_CHARS = 512_000;

export type ParsedGuidanceEvent =
  | { kind: "envelope"; envelope: GuidanceStreamEnvelope }
  | { kind: "parse_error"; line: string };

export async function* parseGuidanceSse(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  signal: AbortSignal,
): AsyncGenerator<ParsedGuidanceEvent, void, unknown> {
  const decoder = new TextDecoder();
  let buffer = "";

  while (!signal.aborted) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const rawBlock = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);

      const lines = rawBlock.split("\n");
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith(":")) continue;
        if (!trimmed.startsWith("data:")) continue;
        const dataPart = trimmed.slice(5).trim();
        if (!dataPart) continue;
        if (dataPart.length > MAX_LINE_CHARS) {
          yield { kind: "parse_error", line: "<line too long>" };
          continue;
        }
        const env = parseStreamEnvelope(`data: ${dataPart}`);
        if (!env) {
          yield { kind: "parse_error", line: dataPart.slice(0, 200) };
          continue;
        }
        yield { kind: "envelope", envelope: env };
      }
    }
  }

  const tail = buffer.trim();
  if (tail && !signal.aborted) {
    for (const line of tail.split("\n")) {
      const t = line.trim();
      if (t.startsWith("data:")) {
        const env = parseStreamEnvelope(t);
        if (env) yield { kind: "envelope", envelope: env };
      }
    }
  }
}

export function summarizeEnvelope(envelope: GuidanceStreamEnvelope): string {
  switch (envelope.event) {
    case "metadata": {
      const m = asMetadataPayload(envelope.data);
      return m ? `metadata (${m.verse_count} verses)` : "metadata (unparsed)";
    }
    case "verses": {
      const v = asVersesPayload(envelope.data);
      return v ? `verses (${v.verses.length})` : "verses (unparsed)";
    }
    case "token": {
      const t = asTokenPayload(envelope.data);
      return t ? `token (${t.text.length} chars)` : "token (unparsed)";
    }
    case "error": {
      const e = asErrorPayload(envelope.data);
      return e ? `error (${e.code})` : "error (unparsed)";
    }
    case "completed":
      return "completed";
    default:
      return envelope.event;
  }
}
