"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchVerseCardsByKeys } from "@/lib/api/verses";
import { PracticeCardFrame, practiceMainClassName } from "@/components/practice/PracticeCardFrame";
import { getPracticePersist } from "@/lib/practice/practiceStorage";
import { isPlaceholderTranslation } from "@/lib/practice/verseQuality";
import type { RetrieveVerseCard } from "@/types/guidance";

type Row = { key: string; verse: RetrieveVerseCard | null; loading: boolean; saved: boolean; learned: boolean };

export function ReviewView() {
  const [rows, setRows] = useState<Row[]>([]);
  const [empty, setEmpty] = useState(true);

  useEffect(() => {
    const p = getPracticePersist();
    const learnedKeys = new Set(p.learned.map((e) => e.citationKey));
    const ordered = [...new Set([...p.savedKeys, ...learnedKeys])];
    setEmpty(ordered.length === 0);
    if (ordered.length === 0) {
      setRows([]);
      return;
    }
    setRows(
      ordered.map((key) => ({
        key,
        verse: null,
        loading: true,
        saved: p.savedKeys.includes(key),
        learned: learnedKeys.has(key),
      })),
    );
    const ac = new AbortController();
    let cancelled = false;
    void fetchVerseCardsByKeys(ordered, ac.signal)
      .then((map) => {
        if (cancelled) return;
        setRows(
          ordered.map((key) => {
            const raw = map[key];
            const verse =
              raw && !isPlaceholderTranslation(raw.translation) ? raw : null;
            return {
              key,
              verse,
              loading: false as const,
              saved: p.savedKeys.includes(key),
              learned: learnedKeys.has(key),
            };
          }),
        );
      })
      .catch(() => {
        if (!cancelled) {
          setRows(
            ordered.map((key) => ({
              key,
              verse: null,
              loading: false as const,
              saved: p.savedKeys.includes(key),
              learned: learnedKeys.has(key),
            })),
          );
        }
      });
    return () => {
      cancelled = true;
      ac.abort();
    };
  }, []);

  return (
    <main className={practiceMainClassName}>
      <header className="mb-7 text-center">
        <h1 className="font-serif text-2xl font-normal tracking-tight text-stone-900">Saved</h1>
        <p className="mx-auto mt-2 max-w-sm text-[13px] leading-relaxed text-stone-600">
          Tap any row to open it in Learn and flip through the full deck from there.
        </p>
      </header>

      {empty ? (
        <div className="rounded-xl border border-dashed border-stone-200/90 bg-stone-50/60 px-5 py-10 text-center">
          <p className="text-sm text-stone-600">Saved and learned verses show up here.</p>
          <Link href="/learn" className="mt-4 inline-block text-sm font-medium gold-text underline-offset-4 hover:underline">
            Learn
          </Link>
        </div>
      ) : (
        <ul className="space-y-2.5">
          {rows.map(({ key, verse, loading, saved, learned }) => {
            const tag = saved && learned ? "Saved · Learned" : saved ? "Saved" : learned ? "Learned" : "";
            return (
              <li key={key}>
                <PracticeCardFrame
                  href={`/learn?key=${encodeURIComponent(key)}`}
                  density="compact"
                  citationKey={key}
                  bodyMinClassName="min-h-0 pr-8"
                >
                  {tag ? (
                    <p className="mb-2 text-[10px] text-stone-500">{tag}</p>
                  ) : null}
                  {loading ? (
                    <p className="text-sm text-stone-500">Loading…</p>
                  ) : verse ? (
                    <div className="space-y-1.5">
                      {verse.sanskrit ? (
                        <p lang="sa" className="devanagari-script line-clamp-2 text-[12px] leading-snug text-stone-800">
                          {verse.sanskrit}
                        </p>
                      ) : null}
                      <p className="line-clamp-2 text-[13px] leading-relaxed text-stone-800">{verse.translation}</p>
                    </div>
                  ) : (
                    <p className="text-sm text-stone-500">Unavailable.</p>
                  )}
                </PracticeCardFrame>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}
