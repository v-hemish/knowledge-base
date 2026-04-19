"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { linkCitationsInText } from "@/lib/guidance/linkCitations";
import { Loader2 } from "lucide-react";

interface ExplanationStreamProps {
  text: string;
  streaming: boolean;
  streamError: { code: string; message: string; fallbackUsed?: boolean } | null;
  parseWarnings: string[];
  /** Card heading (default: Reflection) */
  title?: string;
  /** When set, `citation_key` tokens in the text become links to verse anchors. */
  citationKeys?: string[];
}

export function ExplanationStream({
  text,
  streaming,
  streamError,
  parseWarnings,
  title = "Reflection",
  citationKeys = [],
}: ExplanationStreamProps) {
  const hasContent = text.length > 0 || streamError || parseWarnings.length > 0;

  if (!hasContent && !streaming) {
    return null;
  }

  return (
    <Card className="border-stone-200/80 bg-stone-50/30">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base font-medium text-stone-800">{title}</CardTitle>
          {streaming ? (
            <span className="flex items-center gap-1 text-xs text-stone-500">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Writing…
            </span>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {streamError ? (
          <div className="rounded-md border border-amber-200/80 bg-amber-50/60 px-3 py-2 text-sm text-amber-950">
            <p className="font-medium">Explanation unavailable ({streamError.code})</p>
            <p className="mt-1 text-amber-900/90">{streamError.message}</p>
            {streamError.fallbackUsed ? (
              <p className="mt-2 text-xs text-amber-800/90">Showing fallback text below when provided.</p>
            ) : null}
          </div>
        ) : null}
        {text ? (
          <div className="whitespace-pre-wrap rounded-md bg-white/80 p-4 text-sm leading-relaxed text-stone-800 shadow-inner">
            {citationKeys.length > 0 ? linkCitationsInText(text, citationKeys) : text}
          </div>
        ) : streaming ? (
          <p className="text-sm text-stone-500">Waiting for the first tokens…</p>
        ) : null}
        {parseWarnings.length > 0 ? (
          <details className="text-xs text-stone-500">
            <summary className="cursor-pointer">Parse notes ({parseWarnings.length})</summary>
            <ul className="mt-1 list-inside list-disc">
              {parseWarnings.slice(0, 8).map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </details>
        ) : null}
      </CardContent>
    </Card>
  );
}
