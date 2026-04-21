"use client";

export function ReflectingState({ show }: { show: boolean }) {
  if (!show) return null;

  return (
    <div className="animate-calm-fade rounded-xl bg-stone-100/90 px-3.5 py-3 text-[13px] text-stone-600">
      <div className="flex items-center gap-2.5">
        <div className="flex items-center gap-1.5">
          <span className="animate-reflect-pulse inline-block h-1.5 w-1.5 rounded-full bg-[hsl(var(--gold))]" />
          <span
            className="animate-reflect-pulse inline-block h-1.5 w-1.5 rounded-full bg-[hsl(var(--gold))]"
            style={{ animationDelay: "180ms" }}
          />
          <span
            className="animate-reflect-pulse inline-block h-1.5 w-1.5 rounded-full bg-[hsl(var(--gold))]"
            style={{ animationDelay: "360ms" }}
          />
        </div>
        <p>Retrieving verses…</p>
      </div>
    </div>
  );
}
