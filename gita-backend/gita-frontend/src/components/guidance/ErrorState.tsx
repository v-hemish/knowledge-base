"use client";

import { AlertCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface ErrorStateProps {
  title: string;
  message: string;
  detail?: string;
}

export function ErrorState({ title, message, detail }: ErrorStateProps) {
  return (
    <Card className="border-amber-200/80 bg-amber-50/40">
      <CardContent className="flex gap-3 pt-6">
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" aria-hidden />
        <div className="space-y-1">
          <p className="font-medium text-amber-950">{title}</p>
          <p className="text-sm text-amber-900/90">{message}</p>
          {detail ? (
            <pre className="max-h-40 overflow-auto rounded-md bg-white/60 p-2 text-xs text-stone-700">
              {detail}
            </pre>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
