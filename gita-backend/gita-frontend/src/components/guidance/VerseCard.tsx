"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { slokaFragmentId } from "@/lib/guidance/slokaAnchor";
import type { RetrieveVerseCard, StreamVerseCard } from "@/types/guidance";

type VerseCardProps =
  | { variant: "retrieve"; verse: RetrieveVerseCard }
  | { variant: "stream"; verse: StreamVerseCard };

export function VerseCard(props: VerseCardProps) {
  if (props.variant === "retrieve") {
    const { verse } = props;
    return (
      <article id={slokaFragmentId(verse.citation_key)} className="scroll-mt-6">
      <Card className="overflow-hidden border-stone-200/90 bg-white/90">
        <CardHeader className="border-b border-stone-100 bg-stone-50/50 pb-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <CardTitle className="text-lg text-stone-900">{verse.citation_key}</CardTitle>
            <span className="text-sm text-stone-500">
              Chapter {verse.chapter}, verse {verse.verse}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 pt-5">
          {verse.sanskrit ? (
            <p className="font-serif text-lg leading-relaxed text-stone-900">{verse.sanskrit}</p>
          ) : null}
          {verse.transliteration ? (
            <p className="text-sm italic text-stone-600">{verse.transliteration}</p>
          ) : null}
          <p className="text-base leading-relaxed text-stone-800">{verse.translation}</p>
          <div className="rounded-lg border border-stone-100 bg-stone-50/80 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Why this verse</p>
            <p className="mt-1 text-sm leading-relaxed text-stone-700">{verse.why_selected_short}</p>
          </div>
        </CardContent>
      </Card>
      </article>
    );
  }

  const { verse } = props;
  return (
    <article id={slokaFragmentId(verse.citation_key)} className="scroll-mt-6">
    <Card className="overflow-hidden border-stone-200/90 bg-white/90">
      <CardHeader className="border-b border-stone-100 bg-stone-50/50 pb-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <CardTitle className="text-lg text-stone-900">{verse.citation}</CardTitle>
          <span className="text-sm text-stone-500">
            {verse.citation_key} · Ch. {verse.chapter}, v. {verse.verse}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-5">
        {verse.sanskrit ? (
          <p className="font-serif text-lg leading-relaxed text-stone-900">{verse.sanskrit}</p>
        ) : null}
        {verse.transliteration ? (
          <p className="text-sm italic text-stone-600">{verse.transliteration}</p>
        ) : null}
        <p className="text-base leading-relaxed text-stone-800">{verse.translation}</p>
        {(verse.theme_tags.length > 0 || verse.situation_tags.length > 0) && (
          <div className="flex flex-wrap gap-1.5 text-xs text-stone-500">
            {[...verse.theme_tags, ...verse.situation_tags].map((t) => (
              <span key={t} className="rounded bg-stone-100 px-2 py-0.5">
                {t}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
    </article>
  );
}
