/** Stable fragment id for a verse card (matches `citation_key` like `2.47` → `sloka-2-47`). */
export function slokaFragmentId(citationKey: string): string {
  return `sloka-${citationKey.replace(/\./g, "-")}`;
}
