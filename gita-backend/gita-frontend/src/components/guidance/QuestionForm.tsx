"use client";

import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface QuestionFormProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  busy: boolean;
  disabled?: boolean;
}

export function QuestionForm({ value, onChange, onSubmit, busy, disabled }: QuestionFormProps) {
  const locked = busy || disabled;
  return (
    <div className="space-y-3">
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="What is on your mind?"
        disabled={locked}
        maxLength={2000}
        rows={4}
        aria-label="Your question"
        className="resize-y text-base"
      />
      <Button type="button" onClick={onSubmit} disabled={locked || !value.trim()} className="min-w-[120px]">
        {busy ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Answering…
          </>
        ) : (
          "Ask"
        )}
      </Button>
    </div>
  );
}
