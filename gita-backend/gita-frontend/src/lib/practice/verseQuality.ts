/**
 * Detects rows where the corpus has no real English translation (editorial stubs).
 * Your DB may differ from `canonical_bhagavadgita_gita_io.json` for some keys.
 */
const PLACEHOLDER_SUBSTRINGS = [
  "has not translated this verse",
  "many editions of the bhagavad gita do not contain this verse",
  "total number of verses in the bhagavad gita is 701",
] as const;

export function isPlaceholderTranslation(translation: string | null | undefined): boolean {
  if (!translation) return true;
  const t = translation.trim();
  if (t.length < 24) return true;
  const lower = t.toLowerCase();
  return PLACEHOLDER_SUBSTRINGS.some((s) => lower.includes(s));
}
