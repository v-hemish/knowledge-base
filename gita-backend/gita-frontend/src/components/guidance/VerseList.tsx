"use client";

import type { CSSProperties } from "react";
import { VerseCard } from "./VerseCard";
import type { RetrieveVerseCard, StreamVerseCard } from "@/types/guidance";

interface VerseListProps {
  variant: "retrieve" | "stream";
  retrieveVerses?: RetrieveVerseCard[];
  streamVerses?: StreamVerseCard[];
  animateIn?: boolean;
  staggerMs?: number;
}

export function VerseList({
  variant,
  retrieveVerses,
  streamVerses,
  animateIn = false,
  staggerMs = 140,
}: VerseListProps) {
  if (variant === "retrieve" && retrieveVerses) {
    return (
      <div className="space-y-2.5">
        {retrieveVerses.map((v, idx) => (
          <div
            key={`${v.citation_key}-${v.chapter}-${v.verse}`}
            className={animateIn ? "animate-verse-rise" : undefined}
            style={animateIn ? ({ animationDelay: `${idx * staggerMs}ms` } as CSSProperties) : undefined}
          >
            <VerseCard variant="retrieve" verse={v} />
          </div>
        ))}
      </div>
    );
  }
  if (variant === "stream" && streamVerses) {
    return (
      <div className="space-y-2.5">
        {streamVerses.map((v, idx) => (
          <div
            key={`${v.citation_key}-${v.chapter}-${v.verse}`}
            className={animateIn ? "animate-verse-rise" : undefined}
            style={animateIn ? ({ animationDelay: `${idx * staggerMs}ms` } as CSSProperties) : undefined}
          >
            <VerseCard variant="stream" verse={v} />
          </div>
        ))}
      </div>
    );
  }
  return null;
}
