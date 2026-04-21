"use client";

import type { KeyboardEventHandler, RefObject } from "react";
import { ArrowUp, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface ChatComposerProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  busy: boolean;
  disabled?: boolean;
  /** When set, shows a compact stop control while `busy`. */
  onCancel?: () => void;
  textareaRef?: RefObject<HTMLTextAreaElement | null>;
  className?: string;
}

export function ChatComposer({
  value,
  onChange,
  onSubmit,
  busy,
  disabled,
  onCancel,
  textareaRef,
  className,
}: ChatComposerProps) {
  const locked = busy || disabled;

  const onKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!locked && value.trim()) onSubmit();
    }
  };

  return (
    <div
      className={cn(
        "flex items-end gap-1.5 rounded-2xl border border-stone-200/80 bg-white/95 px-2 py-1.5 shadow-sm shadow-stone-900/[0.04] ring-1 ring-stone-900/[0.03] transition-[box-shadow,border-color] duration-200 focus-within:border-stone-300/90 focus-within:shadow-md focus-within:shadow-stone-900/[0.06]",
        className,
      )}
    >
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Message…"
        disabled={locked}
        maxLength={2000}
        rows={1}
        aria-label="Your question"
        className="min-h-[36px] max-h-[min(40vh,200px)] flex-1 resize-none border-0 bg-transparent px-1.5 py-2 text-[14px] leading-snug text-stone-900 shadow-none placeholder:text-stone-400/85 focus-visible:ring-0"
      />
      {busy && onCancel ? (
        <button
          type="button"
          onClick={onCancel}
          className="mb-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-stone-200/90 bg-stone-50 text-stone-600 transition-colors hover:bg-stone-100 hover:text-stone-900"
          aria-label="Stop generating"
        >
          <Square className="h-3 w-3 fill-current" aria-hidden />
        </button>
      ) : null}
      <Button
        type="button"
        onClick={onSubmit}
        disabled={locked || !value.trim()}
        className="mb-0.5 h-8 w-8 shrink-0 rounded-full bg-stone-900 p-0 text-white shadow-sm transition-transform duration-200 hover:bg-stone-800 hover:scale-[1.03] active:scale-[0.97] disabled:opacity-35"
        aria-label="Send"
      >
        {busy ? (
          <span className="inline-block h-3.5 w-3.5 animate-pulse rounded-full bg-white/80" />
        ) : (
          <ArrowUp className="h-3.5 w-3.5" strokeWidth={2.25} />
        )}
      </Button>
    </div>
  );
}
