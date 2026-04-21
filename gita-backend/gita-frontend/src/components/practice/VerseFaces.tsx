import type { RetrieveVerseCard } from "@/types/guidance";
import { cn } from "@/lib/utils";

/** Front of card: Devanagari + IAST only (recitation face). */
export function VerseSlokaFace({ verse, className }: { verse: RetrieveVerseCard; className?: string }) {
  const hasScript = Boolean(verse.sanskrit?.trim() || verse.transliteration?.trim());
  return (
    <div className={cn("space-y-3", className)}>
      {verse.sanskrit ? (
        <p lang="sa" className="devanagari-script text-[1.12rem] leading-[1.75] text-stone-900 sm:text-[1.2rem]">
          {verse.sanskrit}
        </p>
      ) : null}
      {verse.transliteration ? (
        <p className="text-sm italic leading-relaxed text-[hsl(var(--muted-foreground))] sm:text-[0.95rem]">
          {verse.transliteration}
        </p>
      ) : null}
      {!hasScript ? (
        <p className="text-sm leading-relaxed text-stone-500">No Devanagari text for this verse.</p>
      ) : null}
    </div>
  );
}

/** Back of card: English meaning, optional śloka echo. */
export function VerseMeaningBack({
  verse,
  className,
  compact,
}: {
  verse: RetrieveVerseCard;
  className?: string;
  /** Tighter spacing, no section labels. */
  compact?: boolean;
}) {
  const hasScript = Boolean(verse.sanskrit?.trim() || verse.transliteration?.trim());
  return (
    <div className={cn(compact ? "space-y-3" : "space-y-5", className)}>
      <p className={cn("font-serif leading-relaxed text-stone-900", compact ? "text-[1rem] sm:text-[1.05rem]" : "text-[1.05rem] sm:text-lg")}>
        {verse.translation}
      </p>
      {hasScript ? (
        <div className={cn("border-t border-stone-200/80", compact ? "pt-3" : "pt-4")}>
          {!compact ? (
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500">Śloka</p>
          ) : null}
          {verse.sanskrit ? (
            <p
              lang="sa"
              className={cn(
                "devanagari-script leading-relaxed text-stone-700",
                compact ? "mt-1 text-[0.95rem]" : "mt-2 text-[0.98rem]",
              )}
            >
              {verse.sanskrit}
            </p>
          ) : null}
          {verse.transliteration ? (
            <p className={cn("italic leading-relaxed text-stone-500", compact ? "mt-1.5 text-xs" : "mt-2 text-xs")}>
              {verse.transliteration}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
