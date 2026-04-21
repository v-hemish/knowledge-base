"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight, Check, Bookmark, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchCitationIndex } from "@/lib/api/verses";
import { fetchFirstDisplayableInDeckFrom } from "@/lib/practice/fetchVerse";
import {
  dismissLearnTips,
  getPracticePersist,
  hasLearnTipsDismissed,
  isLearned,
  isSaved,
  markLearned,
  setLastLearnCitationKey,
  toggleSaved,
} from "@/lib/practice/practiceStorage";
import { PracticeCardFrame, practiceMainClassName } from "@/components/practice/PracticeCardFrame";
import { VerseMeaningBack, VerseSlokaFace } from "@/components/practice/VerseFaces";
import type { RetrieveVerseCard } from "@/types/guidance";
import { cn } from "@/lib/utils";

export function LearnDeck() {
  const search = useSearchParams();
  const startKey = search.get("key");

  const [deckKeys, setDeckKeys] = useState<string[] | null>(null);
  const [deckListError, setDeckListError] = useState<string | null>(null);
  const [showTips, setShowTips] = useState(false);

  const swipeX = useRef<number | null>(null);

  useEffect(() => {
    setShowTips(!hasLearnTipsDismissed());
  }, []);

  useEffect(() => {
    const ac = new AbortController();
    setDeckListError(null);
    void fetchCitationIndex(ac.signal)
      .then((keys) => {
        if (ac.signal.aborted) return;
        if (keys.length === 0) {
          setDeckListError("No verses with real translations in the database.");
          setDeckKeys([]);
          return;
        }
        setDeckKeys(keys);
      })
      .catch(() => {
        if (!ac.signal.aborted) {
          setDeckListError("Couldn’t load the verse list.");
          setDeckKeys([]);
        }
      });
    return () => ac.abort();
  }, []);

  const initialIndexResolved = useMemo(() => {
    if (!deckKeys?.length) return 0;
    if (startKey) {
      const i = deckKeys.indexOf(startKey);
      return i >= 0 ? i : 0;
    }
    const last = getPracticePersist().lastLearnCitationKey;
    if (last) {
      const j = deckKeys.indexOf(last);
      if (j >= 0) return j;
    }
    return 0;
  }, [deckKeys, startKey]);

  const [index, setIndex] = useState(0);
  useEffect(() => {
    if (deckKeys?.length) setIndex(initialIndexResolved);
  }, [deckKeys, initialIndexResolved]);

  const deckLen = deckKeys?.length ?? 0;
  const slotKey = deckLen > 0 && deckKeys ? deckKeys[index]! : "—";

  const [verse, setVerse] = useState<RetrieveVerseCard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [learned, setLearned] = useState(false);
  const [face, setFace] = useState<"sloka" | "meaning">("sloka");

  const displayKey = verse?.citation_key ?? slotKey;

  useEffect(() => {
    setSaved(isSaved(displayKey));
    setLearned(isLearned(displayKey));
  }, [displayKey]);

  useEffect(() => {
    if (verse?.citation_key) setLastLearnCitationKey(verse.citation_key);
  }, [verse?.citation_key]);

  useEffect(() => {
    if (!deckKeys?.length) return;
    const ac = new AbortController();
    setLoading(true);
    setError(null);
    setFace("sloka");
    setVerse(null);
    void fetchFirstDisplayableInDeckFrom(index, deckKeys, ac.signal)
      .then((r) => {
        if (ac.signal.aborted) return;
        if (!r) {
          setVerse(null);
          setError("No displayable verse here. Try the next arrow, or check translations.");
          return;
        }
        setVerse(r.verse);
        if (r.deckIndex !== index) setIndex(r.deckIndex);
      })
      .catch(() => {
        if (!ac.signal.aborted) setError("Couldn’t load this verse.");
      })
      .finally(() => {
        if (!ac.signal.aborted) setLoading(false);
      });
    return () => ac.abort();
  }, [index, deckKeys]);

  const go = useCallback(
    (delta: number) => {
      setIndex((i) => {
        const len = deckKeys?.length ?? 0;
        if (len <= 0) return 0;
        const n = i + delta;
        if (n < 0) return len - 1;
        if (n >= len) return 0;
        return n;
      });
    },
    [deckKeys],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.defaultPrevented) return;
      const t = e.target as HTMLElement | null;
      if (t?.closest?.("input, textarea, [contenteditable=true]")) return;
      if (deckLen <= 0) return;

      if (e.key === "ArrowLeft") {
        e.preventDefault();
        go(-1);
        return;
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        go(1);
        return;
      }
      if (e.key === "f" || e.key === "F") {
        if (!loading && verse) {
          e.preventDefault();
          setFace((f) => (f === "sloka" ? "meaning" : "sloka"));
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [deckLen, go, loading, verse]);

  const onSave = useCallback(() => {
    const k = verse?.citation_key ?? slotKey;
    if (k === "—") return;
    const now = toggleSaved(k);
    setSaved(now);
  }, [verse?.citation_key, slotKey]);

  const onLearned = useCallback(() => {
    const k = verse?.citation_key ?? slotKey;
    if (k === "—") return;
    markLearned(k);
    setLearned(true);
    go(1);
  }, [verse?.citation_key, slotKey, go]);

  const onDismissTips = useCallback(() => {
    dismissLearnTips();
    setShowTips(false);
  }, []);

  const savedCount = getPracticePersist().savedKeys.length;

  const deckLoading = deckKeys === null;
  const showDeckError = deckListError && deckKeys !== null;
  const progressPct = deckLen > 0 ? Math.min(100, Math.max(0, ((index + 1) / deckLen) * 100)) : 0;

  return (
    <main className={practiceMainClassName}>
      <header className="mb-5 text-center">
        <h1 className="font-serif text-2xl font-normal tracking-tight text-stone-900">Learn</h1>
        <p className="mx-auto mt-2 max-w-md text-[13px] leading-relaxed text-stone-600">
          Verses follow your text order. Tap the card for English, use arrows to move on, then save or mark learned.
        </p>
        {!deckLoading && !showDeckError && deckLen > 0 ? (
          <div className="mx-auto mt-4 h-1.5 max-w-xs overflow-hidden rounded-full bg-stone-200/90">
            <div
              className="h-full rounded-full bg-[hsl(var(--gold))] transition-[width] duration-300 ease-out"
              style={{ width: `${progressPct}%` }}
              aria-hidden
            />
          </div>
        ) : null}
      </header>

      {showTips && !deckLoading && !showDeckError ? (
        <div className="relative mb-6 rounded-xl border border-stone-200/90 bg-white/90 px-4 py-3.5 text-left shadow-sm ring-1 ring-stone-900/[0.04]">
          <button
            type="button"
            onClick={onDismissTips}
            className="absolute right-2 top-2 rounded-full p-1.5 text-stone-500 transition-colors hover:bg-stone-100 hover:text-stone-800"
            aria-label="Close tips"
          >
            <X className="h-4 w-4" />
          </button>
          <p className="pr-8 text-[11px] font-medium uppercase tracking-[0.14em] text-stone-500">Quick tips</p>
          <ul className="mt-2 space-y-1.5 text-[13px] leading-snug text-stone-700">
            <li>
              <span className="font-medium text-stone-800">Navigate:</span> arrows below, keyboard ← →, or swipe the
              card left / right.
            </li>
            <li>
              <span className="font-medium text-stone-800">Flip:</span> tap the card or press{" "}
              <kbd className="rounded border border-stone-300 bg-stone-50 px-1 py-0.5 font-mono text-[11px] text-stone-800">
                f
              </kbd>
              .
            </li>
            <li>
              <span className="font-medium text-stone-800">Learned</span> saves progress and moves you to the next
              verse.
            </li>
          </ul>
          <Button type="button" variant="secondary" size="sm" className="mt-3 rounded-full" onClick={onDismissTips}>
            Got it
          </Button>
        </div>
      ) : null}

      {deckLoading ? (
        <p className="text-center text-sm text-stone-500">Loading…</p>
      ) : showDeckError ? (
        <p className="text-center text-sm text-red-700/90">{deckListError}</p>
      ) : (
        <>
          <div
            className="touch-pan-y"
            onTouchStart={(e) => {
              swipeX.current = e.touches[0]?.clientX ?? null;
            }}
            onTouchEnd={(e) => {
              const start = swipeX.current;
              swipeX.current = null;
              if (start == null || deckLen <= 0) return;
              const end = e.changedTouches[0]?.clientX;
              if (end == null) return;
              const dx = end - start;
              if (Math.abs(dx) < 56) return;
              if (dx < 0) go(1);
              else go(-1);
              setFace("sloka");
            }}
          >
            <PracticeCardFrame
              interactive
              citationKey={displayKey !== "—" ? displayKey : undefined}
              onClick={() => setFace((f) => (f === "sloka" ? "meaning" : "sloka"))}
              disabled={deckLen <= 0}
              aria-label={face === "sloka" ? "Show meaning" : "Show śloka"}
              bodyMinClassName="min-h-[200px] sm:min-h-[220px]"
              footer={
                <span>
                  Tap to flip · <span className="hidden sm:inline">← → or swipe for next / prev · </span>
                  <kbd className="rounded border border-stone-200 bg-stone-50/90 px-1 py-px font-mono text-[10px]">f</kbd>{" "}
                  flips
                </span>
              }
            >
              <div className="relative">
                <div
                  className={cn(
                    "transition-opacity duration-300 ease-out",
                    face === "sloka" ? "opacity-100" : "pointer-events-none absolute inset-0 opacity-0",
                  )}
                >
                  {loading ? (
                    <p className="text-sm text-stone-500">Loading…</p>
                  ) : error ? (
                    <p className="text-sm text-red-700/90">{error}</p>
                  ) : verse ? (
                    <VerseSlokaFace verse={verse} />
                  ) : null}
                </div>
                <div
                  className={cn(
                    "transition-opacity duration-300 ease-out",
                    face === "meaning" ? "opacity-100" : "pointer-events-none absolute inset-0 opacity-0",
                  )}
                >
                  {verse ? <VerseMeaningBack verse={verse} compact /> : null}
                </div>
              </div>
            </PracticeCardFrame>
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-11 w-11 shrink-0 rounded-full border-stone-200 p-0 sm:h-10 sm:w-10"
              onClick={() => go(-1)}
              disabled={deckLen <= 0}
              aria-label="Previous verse"
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-11 w-11 shrink-0 rounded-full border-stone-200 p-0 sm:h-10 sm:w-10"
              onClick={() => go(1)}
              disabled={deckLen <= 0}
              aria-label="Next verse"
            >
              <ChevronRight className="h-5 w-5" />
            </Button>
            <Button
              type="button"
              variant={saved ? "default" : "outline"}
              size="sm"
              className={cn(
                "h-11 min-w-[5.5rem] rounded-full px-3 sm:h-9",
                saved && "bg-[hsl(var(--gold))] text-stone-900 hover:bg-[hsl(var(--gold))]/90",
              )}
              onClick={onSave}
              disabled={deckLen <= 0 || displayKey === "—"}
            >
              <Bookmark className="mr-1 inline h-3.5 w-3.5" />
              {saved ? "Saved" : "Save"}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-11 min-w-[5.5rem] rounded-full border-[hsl(var(--gold)/0.45)] px-3 gold-text sm:h-9"
              onClick={onLearned}
              disabled={learned || deckLen <= 0 || displayKey === "—"}
            >
              <Check className="mr-1 inline h-3.5 w-3.5" />
              {learned ? "Learned" : "Learn"}
            </Button>
          </div>

          <p className="mt-3 text-center text-[11px] tabular-nums text-stone-500">
            Verse {deckLen > 0 ? index + 1 : 0} of {deckLen}
            {savedCount > 0 ? (
              <>
                {" · "}
                <Link href="/review" className="gold-text underline-offset-2 hover:underline">
                  {savedCount} saved
                </Link>
              </>
            ) : null}
          </p>
        </>
      )}
    </main>
  );
}
