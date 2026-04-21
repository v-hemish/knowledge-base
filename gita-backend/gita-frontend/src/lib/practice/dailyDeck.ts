/**
 * Curated rotation for **Verse of the Day** (`/today`): matches ``starter_verse_pack`` in
 * ``backend/data/gita_daily_practice_app_spec_with_sanskrit.json``. Learn flashcards use
 * ``GET /api/v1/verses/citation-index`` (full DB order) instead.
 */
export const PRACTICE_DECK_CITATION_KEYS: readonly string[] = [
  "2.13",
  "2.14",
  "2.47",
  "3.19",
  "3.35",
  "5.12",
  "6.5",
  "6.6",
  "6.26",
  "12.12",
  "12.13",
  "18.62",
  "18.66",
] as const;

function localDayKey(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** Stable index from calendar day (local timezone). */
export function dayIndexForDate(d: Date): number {
  const [y, mo, da] = localDayKey(d).split("-").map(Number);
  const utc = Date.UTC(y, mo - 1, da);
  return Math.floor(utc / 86_400_000);
}

export function citationKeyForVerseOfTheDay(d: Date = new Date()): string {
  const idx = dayIndexForDate(d);
  return PRACTICE_DECK_CITATION_KEYS[idx % PRACTICE_DECK_CITATION_KEYS.length]!;
}
