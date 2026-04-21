"use client";

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import { Circle, CircleCheck } from "lucide-react";
import { PracticeCardFrame, practiceMainClassName } from "@/components/practice/PracticeCardFrame";
import { VerseMeaningBack, VerseSlokaFace } from "@/components/practice/VerseFaces";
import { ApiError } from "@/lib/api/client";
import { fetchDisplayableVerseForDay } from "@/lib/practice/fetchVerse";
import {
  isVerseOfDayComplete,
  markVerseOfDayComplete,
  unmarkVerseOfDayComplete,
} from "@/lib/practice/practiceStorage";
import type { RetrieveVerseCard } from "@/types/guidance";
import { cn } from "@/lib/utils";

export function TodayView() {
  const today = useMemo(() => new Date(), []);
  const [face, setFace] = useState<"sloka" | "meaning">("sloka");
  const [citationKey, setCitationKey] = useState<string>("");
  const [verse, setVerse] = useState<RetrieveVerseCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [celebrateTick, setCelebrateTick] = useState(0);

  useEffect(() => {
    setDone(isVerseOfDayComplete(today));
  }, [today]);

  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    setError(null);
    setFace("sloka");
    void fetchDisplayableVerseForDay(today, ac.signal)
      .then((r) => {
        if (ac.signal.aborted) return;
        if (!r) {
          setVerse(null);
          setCitationKey("");
          setError("No verse with a real translation for today’s deck. Seed the DB or check translations.");
          return;
        }
        setVerse(r.verse);
        setCitationKey(r.citationKey);
      })
      .catch((e: unknown) => {
        if (ac.signal.aborted) return;
        if (e instanceof ApiError) {
          setError(`Couldn’t load today’s verse (HTTP ${e.status}). Check the API and BACKEND_URL for the Next proxy.`);
          return;
        }
        setError("Couldn’t reach the API. Run `make dev` from gita-backend (sets BACKEND_URL) and restart Next.");
      })
      .finally(() => {
        if (!ac.signal.aborted) setLoading(false);
      });
    return () => ac.abort();
  }, [today]);

  const onToggleComplete = useCallback(() => {
    if (done) {
      unmarkVerseOfDayComplete(today);
      setDone(false);
      return;
    }
    markVerseOfDayComplete(today);
    setDone(true);
    setCelebrateTick((n) => n + 1);
  }, [done, today]);

  /** Mild champagne gold; sheen adds a narrow cool silver specular “zing”, not a silver card. */
  const todayMetallicClass = cn(
    "shadow-[0_10px_28px_-18px_rgba(90,75,55,0.09)]",
    "before:pointer-events-none before:absolute before:inset-0 before:rounded-xl before:content-['']",
    done
      ? [
          "!bg-[linear-gradient(148deg,#fdfaf6_0%,#f2e9d8_26%,#fffdfb_54%,#ebe3d4_100%)]",
          "!ring-[hsl(var(--gold)_/_0.2)]",
          "before:bg-[linear-gradient(122deg,transparent_9%,rgba(255,255,255,0.5)_32%,rgba(226,232,240,0.35)_44%,rgba(255,252,245,0.25)_52%,transparent_86%)]",
        ]
      : [
          "!bg-[linear-gradient(148deg,#fffefb_0%,#faf6ee_24%,#ffffff_52%,#f5efe4_100%)]",
          "!ring-stone-200/75",
          "before:bg-[linear-gradient(122deg,transparent_10%,rgba(255,255,255,0.38)_36%,rgba(203,213,225,0.2)_47%,rgba(255,255,255,0.12)_54%,transparent_88%)]",
        ],
  );

  const toggleFace = useCallback(() => {
    setFace((f) => (f === "sloka" ? "meaning" : "sloka"));
  }, []);

  return (
    <main className={practiceMainClassName}>
      <header className="mb-8 text-center">
        <p className="text-[10px] font-medium uppercase tracking-[0.22em] text-stone-500">Gita Path</p>
        <h1 className="mt-2 font-serif text-2xl font-normal tracking-tight text-stone-900 sm:text-[1.65rem]">
          Today&apos;s verse
        </h1>
        <div className="mx-auto mt-3 max-w-[20rem] space-y-1.5 text-[13px] leading-relaxed text-stone-600">
          <p>Flip the card for the translation, then mark below when you&apos;re done.</p>
          <p>
            For a question, use <span className="font-medium text-stone-700">Reflect</span>—answers follow verses from this
            text.
          </p>
        </div>
      </header>

      {loading ? (
        <p className="text-center text-sm text-stone-500">Loading…</p>
      ) : error ? (
        <p className="text-center text-sm text-red-700/90">{error}</p>
      ) : verse ? (
        <>
          <div className="[perspective:1200px]">
            <div
              className={cn(
                "relative transition-transform duration-500 ease-out [transform-style:preserve-3d]",
                face === "meaning" ? "[transform:rotateY(180deg)]" : "[transform:rotateY(0deg)]",
              )}
            >
              <div className="[backface-visibility:hidden]">
                <PracticeCardFrame
                  interactive
                  citationKey={citationKey || undefined}
                  onClick={toggleFace}
                  aria-label="Show meaning"
                  bodyMinClassName="min-h-[210px] sm:min-h-[230px]"
                  className={todayMetallicClass}
                  footer="Showing śloka"
                >
                  <VerseSlokaFace verse={verse} />
                </PracticeCardFrame>
              </div>

              <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                <PracticeCardFrame
                  interactive
                  citationKey={citationKey || undefined}
                  onClick={toggleFace}
                  aria-label="Show śloka"
                  bodyMinClassName="min-h-[210px] sm:min-h-[230px]"
                  className={todayMetallicClass}
                  footer="Showing meaning"
                >
                  <VerseMeaningBack verse={verse} compact />
                </PracticeCardFrame>
              </div>
            </div>
          </div>

          <div className="relative mt-7 flex justify-center">
            {celebrateTick > 0 && done ? (
              <div key={celebrateTick} className="pointer-events-none absolute -top-10 left-1/2 h-0 w-0" aria-hidden>
                {Array.from({ length: 18 }).map((_, i) => (
                  <span
                    key={i}
                    className="today-sprinkle absolute left-0 top-0 h-1.5 w-1.5 rounded-sm bg-gradient-to-br from-[hsl(var(--gold)_/_0.75)] via-white to-slate-300"
                    style={
                      {
                        "--sprinkle-angle": `${i * 20}deg`,
                        "--sprinkle-dist": `${40 + (i % 4) * 10}px`,
                        "--sprinkle-delay": `${(i % 6) * 28}ms`,
                      } as CSSProperties
                    }
                  />
                ))}
              </div>
            ) : null}
            <button
              type="button"
              onClick={onToggleComplete}
              aria-label={done ? "Undo today’s mark" : "Mark today complete"}
              className={cn(
                "inline-flex h-10 w-10 items-center justify-center rounded-full border transition-colors",
                done
                  ? "border-[hsl(var(--gold))] bg-[hsl(var(--gold)_/_0.14)] text-[hsl(var(--gold))] hover:bg-[hsl(var(--gold)_/_0.22)]"
                  : "border-stone-300 bg-white text-stone-400 hover:border-stone-400 hover:text-stone-600",
              )}
            >
              {done ? (
                <CircleCheck className="h-5 w-5" strokeWidth={1.75} aria-hidden />
              ) : (
                <Circle className="h-5 w-5" strokeWidth={1.75} aria-hidden />
              )}
            </button>
          </div>
          {done ? (
            <p className="mt-4 text-center text-[12px] text-stone-500">Come back tomorrow.</p>
          ) : null}
        </>
      ) : null}
    </main>
  );
}
