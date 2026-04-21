import type { UseGuidanceStreamState } from "@/hooks/useGuidanceStream";
import type { StreamMetadataPayload, StreamVerseCard } from "@/types/guidance";

/** One completed user question + model response snapshot (client-only history). */
export type GuidanceTurnArchive = {
  id: string;
  prompt: string;
  phase: "completed" | "error" | "cancelled";
  metadata: StreamMetadataPayload | null;
  explanation: string;
  verses: StreamVerseCard[];
  streamError: UseGuidanceStreamState["streamError"];
  parseWarnings: string[];
  transportError: string | null;
};

export function shouldFlushGuidanceTurn(prompt: string, s: UseGuidanceStreamState): boolean {
  const p = prompt.trim();
  if (!p) return false;
  if (s.phase === "connecting" || s.phase === "streaming") return false;
  if (
    s.phase === "idle" &&
    !s.explanation.trim() &&
    s.verses.length === 0 &&
    !s.streamError &&
    !s.transportError
  ) {
    return false;
  }
  return true;
}

export function buildGuidanceTurnArchive(id: string, prompt: string, s: UseGuidanceStreamState): GuidanceTurnArchive {
  const phase: GuidanceTurnArchive["phase"] =
    s.phase === "cancelled"
      ? "cancelled"
      : s.phase === "error" || s.transportError
        ? "error"
        : "completed";

  return {
    id,
    prompt: prompt.trim(),
    phase,
    metadata: s.metadata,
    explanation: s.explanation,
    verses: s.verses,
    streamError: s.streamError,
    parseWarnings: s.parseWarnings,
    transportError: s.transportError,
  };
}
