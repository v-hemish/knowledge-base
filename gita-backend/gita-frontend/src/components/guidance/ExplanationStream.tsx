"use client";

import { useEffect, useMemo, useState } from "react";
import { linkCitationsInText } from "@/lib/guidance/linkCitations";

/** Split into “words” (non-whitespace + following whitespace) for GPT-like word reveal. */
function tokenizeWords(s: string): string[] {
  if (!s) return [];
  return s.match(/[^\s]+\s*/g) ?? [];
}

interface ExplanationStreamProps {
  text: string;
  streaming: boolean;
  reveal?: boolean;
  streamError: { code: string; message: string; fallbackUsed?: boolean } | null;
  parseWarnings: string[];
  title?: string;
  citationKeys?: string[];
  /** Milliseconds between each revealed word while catching up to `text`. */
  wordIntervalMs?: number;
  /** Chat thread: no section header, tighter prose (ChatGPT-style). */
  chatMode?: boolean;
}

export function ExplanationStream({
  text,
  streaming,
  reveal = true,
  streamError,
  parseWarnings,
  title = "Guidance",
  citationKeys = [],
  wordIntervalMs = 72,
  chatMode = false,
}: ExplanationStreamProps) {
  const words = useMemo(() => tokenizeWords(text), [text]);
  const [visibleWordCount, setVisibleWordCount] = useState(0);

  useEffect(() => {
    if (!text) setVisibleWordCount(0);
  }, [text]);

  useEffect(() => {
    if (!streaming && words.length > 0) {
      setVisibleWordCount(words.length);
    }
  }, [streaming, words.length]);

  useEffect(() => {
    if (!reveal) {
      setVisibleWordCount(0);
      return;
    }
    if (words.length === 0) {
      setVisibleWordCount(0);
      return;
    }
    setVisibleWordCount((c) => Math.min(c, words.length));
  }, [reveal, words.length]);

  useEffect(() => {
    if (!reveal) return;
    if (visibleWordCount >= words.length) return;
    if (wordIntervalMs <= 0) {
      setVisibleWordCount(words.length);
      return;
    }
    const id = window.setTimeout(() => {
      setVisibleWordCount((c) => Math.min(c + 1, words.length));
    }, wordIntervalMs);
    return () => window.clearTimeout(id);
  }, [reveal, visibleWordCount, words.length, wordIntervalMs]);

  const renderedText = words.slice(0, visibleWordCount).join("");

  const linkedContent = useMemo(() => {
    if (!renderedText) return null;
    return citationKeys.length > 0 ? linkCitationsInText(renderedText, citationKeys) : renderedText;
  }, [renderedText, citationKeys]);

  const hasContent = text.length > 0 || streamError || parseWarnings.length > 0;
  const showShell = reveal && (hasContent || streaming);

  if (!showShell) {
    return null;
  }

  return (
    <div className={chatMode ? "space-y-2.5" : "space-y-3.5"}>
      {chatMode ? (
        <h2 className="sr-only">{title}</h2>
      ) : (
        <div className="flex items-center justify-between gap-2 px-0.5">
          <h2 className="text-[10px] font-medium uppercase tracking-[0.18em] text-stone-500">{title}</h2>
          {streaming && visibleWordCount < words.length ? (
            <span className="flex items-center gap-1.5 text-[11px] text-stone-400">
              <span className="animate-reflect-pulse inline-block h-1 w-1 rounded-full bg-[hsl(var(--gold))]" />
              …
            </span>
          ) : null}
        </div>
      )}
      {chatMode && streaming && visibleWordCount < words.length ? (
        <div className="flex justify-end">
          <span className="flex items-center gap-1.5 text-[11px] text-stone-400">
            <span className="animate-reflect-pulse inline-block h-1 w-1 rounded-full bg-[hsl(var(--gold))]" />
            …
          </span>
        </div>
      ) : null}

      {streamError ? (
        <div className="rounded-lg border border-amber-200/80 bg-amber-50/50 px-3 py-2 text-sm text-amber-950">
          <p className="text-[13px] leading-snug">
            <span className="font-medium">{streamError.code}:</span> {streamError.message}
          </p>
          {streamError.fallbackUsed ? <p className="mt-1 text-[11px] text-amber-900/85">Using fallback text.</p> : null}
        </div>
      ) : null}

      {renderedText ? (
        <div
          className={
            chatMode
              ? "whitespace-pre-wrap text-[15px] leading-[1.72] tracking-[-0.01em] text-stone-800 sm:text-[16px] sm:leading-[1.7]"
              : "whitespace-pre-wrap text-[17px] leading-[1.78] tracking-[-0.01em] text-stone-800 sm:text-[18px] sm:leading-[1.76]"
          }
        >
          {linkedContent}
        </div>
      ) : streaming ? (
        <p className="text-sm text-stone-400">…</p>
      ) : null}

      {parseWarnings.length > 0 ? (
        <details className="text-[11px] text-stone-500">
          <summary className="cursor-pointer">Details ({parseWarnings.length})</summary>
          <ul className="mt-1 list-inside list-disc">
            {parseWarnings.slice(0, 8).map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}
