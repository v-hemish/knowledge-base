/** Remove MVP corpus placeholders like ``[SEED]`` from verse fields shown in the UI. */
export function stripSeedMarkers(value: string | null | undefined): string {
  if (!value) return "";
  return value.replace(/\[SEED\]\s*/gi, "").trim();
}
