"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { postGuidanceStream } from "@/lib/api/guidance";
import {
  asErrorPayload,
  asMetadataPayload,
  asTokenPayload,
  asVersesPayload,
} from "@/lib/api/adapters";
import { parseGuidanceSse } from "@/lib/sse/guidanceStream";
import type { StreamMetadataPayload, StreamVerseCard } from "@/types/guidance";

export type StreamPhase = "idle" | "connecting" | "streaming" | "completed" | "error" | "cancelled";

export interface UseGuidanceStreamState {
  phase: StreamPhase;
  metadata: StreamMetadataPayload | null;
  verses: StreamVerseCard[];
  explanation: string;
  streamError: { code: string; message: string; fallbackUsed?: boolean } | null;
  transportError: string | null;
  parseWarnings: string[];
}

const initialState: UseGuidanceStreamState = {
  phase: "idle",
  metadata: null,
  verses: [],
  explanation: "",
  streamError: null,
  transportError: null,
  parseWarnings: [],
};

export function useGuidanceStream() {
  const [state, setState] = useState<UseGuidanceStreamState>(initialState);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setState(initialState);
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setState((s) => ({
      ...s,
      phase: "cancelled",
    }));
  }, []);

  const start = useCallback(async (query: string) => {
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;

    setState({
      ...initialState,
      phase: "connecting",
    });

    try {
      const res = await postGuidanceStream(query, ac.signal);
      const reader = res.body!.getReader();

      setState((s) => ({ ...s, phase: "streaming" }));

      for await (const ev of parseGuidanceSse(reader, ac.signal)) {
        if (ev.kind === "parse_error") {
          setState((s) => ({
            ...s,
            parseWarnings: [...s.parseWarnings, ev.line],
          }));
          continue;
        }
        const { envelope } = ev;
        switch (envelope.event) {
          case "metadata": {
            const m = asMetadataPayload(envelope.data);
            if (m) setState((s) => ({ ...s, metadata: m }));
            break;
          }
          case "verses": {
            const v = asVersesPayload(envelope.data);
            if (v) setState((s) => ({ ...s, verses: v.verses }));
            break;
          }
          case "token": {
            const t = asTokenPayload(envelope.data);
            if (t) {
              setState((s) => ({ ...s, explanation: s.explanation + t.text }));
            }
            break;
          }
          case "error": {
            const e = asErrorPayload(envelope.data);
            if (e) {
              setState((s) => ({
                ...s,
                streamError: {
                  code: e.code,
                  message: e.message,
                  fallbackUsed: e.fallback_used,
                },
              }));
            }
            break;
          }
          case "completed":
            setState((s) => ({ ...s, phase: "completed" }));
            break;
          default:
            break;
        }
      }

      setState((s) => {
        if (s.phase === "streaming") return { ...s, phase: "completed" };
        return s;
      });
    } catch (e: unknown) {
      if (ac.signal.aborted) {
        setState((s) => ({ ...s, phase: "cancelled" }));
        return;
      }
      const msg = e instanceof Error ? e.message : String(e);
      setState((s) => ({
        ...s,
        phase: "error",
        transportError: msg,
      }));
    } finally {
      if (abortRef.current === ac) {
        abortRef.current = null;
      }
    }
  }, []);

  const isBusy = state.phase === "connecting" || state.phase === "streaming";

  return useMemo(
    () => ({ state, start, cancel, reset, isBusy }),
    [state, start, cancel, reset, isBusy],
  );
}
