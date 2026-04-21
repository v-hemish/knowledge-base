"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useGuidanceStream } from "@/hooks/useGuidanceStream";
import { VerseList } from "./VerseList";
import { ExplanationStream } from "./ExplanationStream";
import { ErrorState } from "./ErrorState";
import { Button } from "@/components/ui/button";
import { ReflectingState } from "./ReflectingState";
import { ChatComposer } from "./ChatComposer";
import { buildGuidanceTurnArchive, shouldFlushGuidanceTurn, type GuidanceTurnArchive } from "@/lib/guidance/turnArchive";
import { cn } from "@/lib/utils";

/** Pause after stream ends before verse cards mount (snappier than stacking during tokens). */
const VERSES_AFTER_STREAM_PAUSE_MS = 320;
const VERSE_CARD_STAGGER_MS = 200;
const GUIDANCE_WORD_MS = 48;

type GuidanceAppProps = {
  /** Chat as primary vs tab with bottom nav (extra bottom inset). */
  variant?: "primary" | "companion";
};

function UserBubble({ children }: { children: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[min(88%,34rem)] rounded-2xl rounded-br-md bg-stone-900 px-4 py-2.5 text-[15px] leading-relaxed text-stone-50 shadow-md shadow-stone-900/15">
        {children}
      </div>
    </div>
  );
}

function AssistantShell({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "w-full max-w-[min(100%,40rem)] rounded-2xl rounded-bl-md border border-stone-200/70 bg-white/95 px-4 py-3.5 shadow-md shadow-stone-900/[0.04] ring-1 ring-stone-900/[0.025] backdrop-blur-sm",
        className,
      )}
    >
      {children}
    </div>
  );
}

function ArchivedTurn({ turn }: { turn: GuidanceTurnArchive }) {
  const citationKeys = turn.verses.map((v) => v.citation_key).filter(Boolean);
  const title = turn.metadata?.verse_count === 0 ? "Note" : "Guidance";

  return (
    <div className="space-y-3">
      <UserBubble>{turn.prompt}</UserBubble>
      <div className="flex justify-start">
        <div className="w-full max-w-[min(100%,40rem)] space-y-4">
          {turn.transportError ? (
            <ErrorState title="Couldn’t connect" message={turn.transportError} />
          ) : null}
          <AssistantShell>
            <ExplanationStream
              chatMode
              title={title}
              text={turn.explanation}
              streaming={false}
              reveal
              streamError={turn.streamError}
              parseWarnings={turn.parseWarnings}
              citationKeys={citationKeys}
              wordIntervalMs={0}
            />
          </AssistantShell>
          {turn.verses.length > 0 ? (
            <VerseList variant="stream" streamVerses={turn.verses} animateIn={false} staggerMs={0} />
          ) : null}
          {turn.phase === "cancelled" ? <p className="text-[11px] text-stone-500">Stopped.</p> : null}
        </div>
      </div>
    </div>
  );
}

export function GuidanceApp({ variant = "primary" }: GuidanceAppProps) {
  const [question, setQuestion] = useState("");
  const [activePrompt, setActivePrompt] = useState("");
  const [archive, setArchive] = useState<GuidanceTurnArchive[]>([]);
  const [showVersesStage, setShowVersesStage] = useState(false);
  const { state: streamState, start, cancel, reset, isBusy } = useGuidanceStream();

  const scrollEndRef = useRef<HTMLDivElement>(null);
  const streamRef = useRef(streamState);
  streamRef.current = streamState;
  const companion = variant === "companion";

  const citationKeys = useMemo(
    () => streamState.verses.map((v) => v.citation_key).filter(Boolean),
    [streamState.verses],
  );

  const showResults =
    streamState.phase !== "idle" ||
    streamState.verses.length > 0 ||
    streamState.explanation.length > 0 ||
    streamState.metadata !== null ||
    streamState.streamError !== null;

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [
    scrollToBottom,
    archive.length,
    streamState.explanation,
    streamState.phase,
    streamState.verses.length,
    showVersesStage,
    activePrompt,
  ]);

  const handleNewChat = useCallback(() => {
    setArchive([]);
    setActivePrompt("");
    setQuestion("");
    setShowVersesStage(false);
    reset();
  }, [reset]);

  const handleAsk = useCallback(async () => {
    const q = question.trim();
    if (!q) return;

    const prevPrompt = activePrompt;
    const snap = streamRef.current;
    if (shouldFlushGuidanceTurn(prevPrompt, snap)) {
      setArchive((a) => [...a, buildGuidanceTurnArchive(crypto.randomUUID(), prevPrompt, snap)]);
    }

    setQuestion("");
    setActivePrompt(q);
    setShowVersesStage(false);
    await start(q);
  }, [question, activePrompt, start]);

  useEffect(() => {
    if (streamState.verses.length === 0) {
      setShowVersesStage(false);
      return;
    }
    const streamFinished =
      streamState.phase === "completed" ||
      streamState.phase === "cancelled" ||
      streamState.phase === "error";
    if (!streamFinished) {
      setShowVersesStage(false);
      return;
    }
    const t = window.setTimeout(() => setShowVersesStage(true), VERSES_AFTER_STREAM_PAUSE_MS);
    return () => window.clearTimeout(t);
  }, [streamState.verses.length, streamState.phase]);

  const verseCountMeta = streamState.metadata?.verse_count;
  const expectingVerseCards = verseCountMeta === undefined ? true : verseCountMeta > 0;
  const showReflecting =
    expectingVerseCards &&
    (streamState.phase === "connecting" ||
      (streamState.phase === "streaming" &&
        streamState.metadata === null &&
        streamState.verses.length === 0));

  const canNewChat = archive.length > 0 || activePrompt || showResults;

  /** Slim floating composer sits above tab bar (companion) or screen bottom (primary). */
  const composerBottom = companion
    ? "bottom-[calc(4.35rem+env(safe-area-inset-bottom))]"
    : "bottom-[max(0.35rem,env(safe-area-inset-bottom))]";

  const threadBottomPad = companion
    ? "pb-[calc(8.75rem+env(safe-area-inset-bottom))]"
    : "pb-[calc(5.25rem+env(safe-area-inset-bottom))]";

  const emptyHint = !archive.length && !activePrompt && !showResults;

  return (
    <main className="flex min-h-[100dvh] flex-col bg-gradient-to-b from-stone-100/90 via-white to-stone-50">
      <header
        className={cn(
          "sticky top-0 z-20 flex items-center border-b border-stone-200/70 bg-white/80 px-4 py-2.5 backdrop-blur-xl sm:px-5",
          companion ? "justify-end" : "justify-between gap-3",
        )}
      >
        {!companion ? (
          <div className="min-w-0">
            <h1 className="truncate font-serif text-lg font-normal tracking-tight text-stone-900 sm:text-xl">
              Reflect
            </h1>
          </div>
        ) : null}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="shrink-0 rounded-full text-[13px] text-stone-600 hover:bg-stone-100 hover:text-stone-900"
          onClick={handleNewChat}
          disabled={!canNewChat || isBusy}
        >
          New conversation
        </Button>
      </header>

      <div className={cn("min-h-0 flex-1 overflow-y-auto overscroll-y-contain", threadBottomPad)}>
        <div className="mx-auto max-w-3xl space-y-6 px-4 py-5 sm:px-5">
          {archive.map((turn) => (
            <ArchivedTurn key={turn.id} turn={turn} />
          ))}

          {activePrompt ? (
            <div className="space-y-3">
              <UserBubble>{activePrompt}</UserBubble>
              <div className="flex justify-start">
                <div className="w-full max-w-[min(100%,40rem)] space-y-4">
                  {streamState.transportError ? (
                    <ErrorState title="Couldn’t connect" message={streamState.transportError} />
                  ) : null}

                  {showReflecting ||
                  streamState.phase === "connecting" ||
                  streamState.metadata ||
                  streamState.explanation ||
                  streamState.streamError ? (
                    <AssistantShell className={showReflecting ? "py-3" : undefined}>
                      {showReflecting ? <ReflectingState show /> : null}
                      {!showReflecting && streamState.phase === "connecting" && !streamState.metadata ? (
                        <p className="text-sm text-stone-400">…</p>
                      ) : null}
                      {streamState.metadata || streamState.streamError || streamState.explanation ? (
                        <ExplanationStream
                          chatMode
                          title={
                            streamState.metadata?.verse_count === 0
                              ? "Note"
                              : "Guidance"
                          }
                          text={streamState.explanation}
                          streaming={streamState.phase === "streaming"}
                          reveal
                          streamError={streamState.streamError}
                          parseWarnings={streamState.parseWarnings}
                          citationKeys={citationKeys}
                          wordIntervalMs={GUIDANCE_WORD_MS}
                        />
                      ) : null}
                    </AssistantShell>
                  ) : null}

                  {streamState.phase === "cancelled" && !showReflecting ? (
                    <p className="text-[11px] text-stone-500">Stopped.</p>
                  ) : null}

                  {streamState.verses.length > 0 && showVersesStage ? (
                    <section aria-label="Verses cited">
                      <h2 className="sr-only">Verses</h2>
                      <VerseList
                        variant="stream"
                        streamVerses={streamState.verses}
                        animateIn
                        staggerMs={VERSE_CARD_STAGGER_MS}
                      />
                    </section>
                  ) : null}
                </div>
              </div>
            </div>
          ) : null}

          {emptyHint ? (
            <div className="relative -mx-4 min-h-[min(68vh,36rem)] overflow-hidden rounded-none border-y border-stone-200/55 bg-gradient-to-b from-gold-soft/50 via-white/85 to-stone-100/50 px-5 py-14 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.6)] sm:-mx-5 sm:min-h-[min(70vh,38rem)] sm:rounded-2xl sm:border sm:border-stone-200/50 sm:py-16">
              <div
                className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_95%_55%_at_50%_0%,rgba(255,255,255,0.92),transparent_58%)]"
                aria-hidden
              />
              <p
                className="pointer-events-none absolute left-1/2 top-[8%] w-full max-w-3xl -translate-x-1/2 select-none px-4 text-center font-serif text-[clamp(2.75rem,11vw,5rem)] font-extralight leading-[0.95] tracking-[-0.03em] text-stone-800/[0.055] sm:top-[10%]"
                aria-hidden
              >
                Guided by
                <br />
                the Gita
              </p>
              <div className="relative mx-auto flex max-w-lg flex-col items-center gap-8 text-center">
                <span
                  className="block h-px w-16 bg-gradient-to-r from-transparent via-[hsl(var(--gold))]/45 to-transparent"
                  aria-hidden
                />
                <div className="space-y-5 px-1">
                  <h2 className="font-serif text-[1.75rem] font-light leading-snug tracking-[-0.02em] text-stone-800 sm:text-[2rem]">
                    Guided by the Gita
                  </h2>
                  <p className="text-[14px] font-light leading-[1.75] tracking-[0.01em] text-stone-600 sm:text-[15px]">
                    Share what is on your heart or mind. Each response is shaped from the Bhagavad Gita—rooted in verse,
                    interpreted gently, and offered with clarity rather than generic chat.
                  </p>
                </div>
              </div>
            </div>
          ) : null}

          <div ref={scrollEndRef} className="h-px w-full shrink-0" aria-hidden />
        </div>
      </div>

      <div
        className={cn(
          "pointer-events-none fixed inset-x-0 z-30 flex justify-center px-3 sm:px-4",
          composerBottom,
        )}
      >
        <div className="pointer-events-auto w-full max-w-3xl bg-gradient-to-t from-white via-white/92 to-transparent pb-0.5 pt-5">
          <ChatComposer
            value={question}
            onChange={setQuestion}
            onSubmit={() => void handleAsk()}
            busy={isBusy}
            onCancel={cancel}
          />
        </div>
      </div>
    </main>
  );
}
