"use client";

import { useCallback, useMemo, useState } from "react";
import { useGuidanceStream } from "@/hooks/useGuidanceStream";
import { QuestionForm } from "./QuestionForm";
import { VerseList } from "./VerseList";
import { ExplanationStream } from "./ExplanationStream";
import { ErrorState } from "./ErrorState";
import { Button } from "@/components/ui/button";

export function GuidanceApp() {
  const [question, setQuestion] = useState("");
  const { state: streamState, start, cancel, reset, isBusy } = useGuidanceStream();

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

  const handleAsk = useCallback(async () => {
    const q = question.trim();
    if (!q) return;
    await start(q);
  }, [question, start]);

  const handleClear = useCallback(() => {
    setQuestion("");
    reset();
  }, [reset]);

  return (
    <main className="mx-auto max-w-xl px-4 py-8 sm:py-10">
      <h1 className="mb-6 text-center font-serif text-xl text-stone-900 sm:text-2xl">Ask the Gita</h1>

      <div className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
        <QuestionForm
          value={question}
          onChange={setQuestion}
          onSubmit={() => void handleAsk()}
          busy={isBusy}
        />
        <div className="mt-3 flex justify-center gap-2">
          {isBusy ? (
            <Button type="button" variant="outline" size="sm" onClick={cancel}>
              Stop
            </Button>
          ) : null}
          {!isBusy && (question.trim() || showResults) ? (
            <Button type="button" variant="ghost" size="sm" onClick={handleClear}>
              Clear
            </Button>
          ) : null}
        </div>
      </div>

      {streamState.transportError ? (
        <div className="mt-6">
          <ErrorState title="Something went wrong" message={streamState.transportError} />
        </div>
      ) : null}

      {showResults ? (
        <div className="mt-8 space-y-8">
          {streamState.phase === "cancelled" ? (
            <p className="text-center text-sm text-stone-500">Stopped.</p>
          ) : null}

          <section className="space-y-3">
            <h2 className="text-center text-xs font-medium uppercase tracking-wide text-stone-500">
              Verses
            </h2>
            {streamState.verses.length > 0 ? (
              <VerseList variant="stream" streamVerses={streamState.verses} />
            ) : isBusy ? (
              <p className="text-center text-sm text-stone-400">Loading verses…</p>
            ) : streamState.phase === "completed" && streamState.verses.length === 0 ? (
              <p className="text-center text-sm text-stone-600">
                No verses matched. Try different words or check the corpus on the server.
              </p>
            ) : null}
          </section>

          <ExplanationStream
            title="Guidance"
            text={streamState.explanation}
            streaming={streamState.phase === "streaming"}
            streamError={streamState.streamError}
            parseWarnings={streamState.parseWarnings}
            citationKeys={citationKeys}
          />
        </div>
      ) : null}
    </main>
  );
}
