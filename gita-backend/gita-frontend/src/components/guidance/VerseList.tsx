"use client";

import { VerseCard } from "./VerseCard";
import type { RetrieveVerseCard, StreamVerseCard } from "@/types/guidance";

interface VerseListProps {
  variant: "retrieve" | "stream";
  retrieveVerses?: RetrieveVerseCard[];
  streamVerses?: StreamVerseCard[];
}

export function VerseList({ variant, retrieveVerses, streamVerses }: VerseListProps) {
  if (variant === "retrieve" && retrieveVerses) {
    return (
      <div className="space-y-4">
        {retrieveVerses.map((v) => (
          <VerseCard key={`${v.citation_key}-${v.chapter}-${v.verse}`} variant="retrieve" verse={v} />
        ))}
      </div>
    );
  }
  if (variant === "stream" && streamVerses) {
    return (
      <div className="space-y-4">
        {streamVerses.map((v) => (
          <VerseCard
            key={`${v.citation_key}-${v.chapter}-${v.verse}`}
            variant="stream"
            verse={v}
          />
        ))}
      </div>
    );
  }
  return null;
}
