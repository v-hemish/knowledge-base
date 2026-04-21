/**
 * Types aligned with the FastAPI backend (`app/schemas/guidance_retrieve.py`,
 * `app/schemas/guidance.py`). If the API shape drifts, adjust `src/lib/api/adapters.ts`.
 */

export type ExplanationStatus = "verses_only" | "no_hits";

/** POST /api/v1/guidance/retrieve response */
export interface RetrieveVerseCard {
  citation_key: string;
  chapter: number;
  verse: number;
  sanskrit: string | null;
  transliteration: string | null;
  translation: string;
  why_selected_short: string;
}

export interface RetrieveGuidanceResponse {
  query: string;
  selected_verses: RetrieveVerseCard[];
  reflection_prompt: string | null;
  explanation_status: ExplanationStatus;
}

/** POST /api/v1/guidance/stream — `verses` event payload */
export interface StreamVerseCard {
  chapter: number;
  verse: number;
  citation_key: string;
  citation: string;
  translation: string;
  sanskrit: string | null;
  transliteration: string | null;
  theme_tags: string[];
  situation_tags: string[];
  use_with_care_tags: string[];
  translation_source: string | null;
}

export type GuidanceStreamEventName =
  | "metadata"
  | "verses"
  | "token"
  | "error"
  | "completed";

/** Envelope: one JSON object per SSE `data:` line */
export interface GuidanceStreamEnvelope {
  event: GuidanceStreamEventName;
  data: Record<string, unknown>;
}

export interface StreamMetadataPayload {
  query: string;
  model: string;
  verse_count: number;
}

export interface StreamVersesPayload {
  verses: StreamVerseCard[];
}

export interface StreamTokenPayload {
  text: string;
}

export interface StreamErrorPayload {
  code: string;
  message: string;
  fallback_used?: boolean;
}
