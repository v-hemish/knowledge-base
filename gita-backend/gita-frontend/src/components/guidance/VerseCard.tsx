"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { slokaFragmentId } from "@/lib/guidance/slokaAnchor";
import { stripSeedMarkers } from "@/lib/guidance/stripSeedMarkers";
import type { RetrieveVerseCard, StreamVerseCard } from "@/types/guidance";

type VerseCardProps =
  | { variant: "retrieve"; verse: RetrieveVerseCard; className?: string }
  | { variant: "stream"; verse: StreamVerseCard; className?: string };

export function VerseCard(props: VerseCardProps) {
  if (props.variant === "retrieve") {
    const { verse, className } = props;
    return (
      <article id={slokaFragmentId(verse.citation_key)} className={`scroll-mt-28 ${className ?? ""}`}>
        <Card className="overflow-hidden border-0 bg-gradient-to-br from-white via-gold-soft/15 to-white shadow-[0_8px_24px_-16px_rgba(0,0,0,0.12)] ring-1 ring-stone-200/60">
          <CardHeader className="border-b border-stone-200/50 bg-white/50 px-4 py-2.5">
            <CardTitle className="text-sm font-semibold tracking-tight text-stone-900">
              <span className="gold-text">{verse.citation_key}</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2.5 px-4 py-3.5">
            {verse.sanskrit ? (
              <p className="font-serif text-[13px] leading-relaxed text-stone-900">
                {stripSeedMarkers(verse.sanskrit)}
              </p>
            ) : null}
            {verse.transliteration ? (
              <p className="text-[12px] italic leading-relaxed text-stone-500">
                {stripSeedMarkers(verse.transliteration)}
              </p>
            ) : null}
            <p className="text-[13px] leading-relaxed text-stone-800">{stripSeedMarkers(verse.translation)}</p>
            <div className="rounded-lg bg-white/70 px-3 py-2 ring-1 ring-stone-200/40">
              <p className="text-[11px] leading-relaxed text-stone-600">{verse.why_selected_short}</p>
            </div>
          </CardContent>
        </Card>
      </article>
    );
  }

  const { verse, className } = props;
  const translation = stripSeedMarkers(verse.translation);
  const sanskrit = verse.sanskrit ? stripSeedMarkers(verse.sanskrit) : "";
  const transliteration = verse.transliteration ? stripSeedMarkers(verse.transliteration) : "";
  const label = verse.citation?.trim() || `${verse.chapter}.${verse.verse}`;
  const id = slokaFragmentId(verse.citation_key);

  return (
    <article id={id} className={`scroll-mt-24 overflow-hidden rounded-xl ${className ?? ""}`}>
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-white via-gold-soft/20 to-white shadow-[0_10px_28px_-18px_rgba(0,0,0,0.14)] ring-1 ring-stone-200/50">
        <div
          className="pointer-events-none absolute inset-y-2 left-0 w-0.5 rounded-full bg-gradient-to-b from-gold via-gold/75 to-gold/35"
          aria-hidden
        />

        <div className="relative pl-4 pr-3 pb-3 pt-2.5 sm:pl-4 sm:pr-3.5">
          <div className="flex flex-wrap items-center justify-between gap-1.5">
            <p className="font-serif text-base font-semibold tracking-tight text-stone-900">{label}</p>
            <span className="rounded-full bg-gold-soft/45 px-2 py-0.5 text-[9px] font-medium tabular-nums text-stone-600 ring-1 ring-gold/20">
              {verse.chapter}.{verse.verse}
            </span>
          </div>

          {sanskrit ? (
            <p className="mt-2 font-serif text-[12px] leading-snug text-stone-900">{sanskrit}</p>
          ) : null}
          {transliteration ? (
            <p className="mt-1 text-[10px] italic leading-snug text-stone-500">{transliteration}</p>
          ) : null}

          <div className="my-2 h-px bg-gradient-to-r from-gold/35 via-stone-200/80 to-gold/25" aria-hidden />

          <p className="text-[11px] leading-relaxed text-stone-800">{translation}</p>
        </div>
      </div>
    </article>
  );
}
