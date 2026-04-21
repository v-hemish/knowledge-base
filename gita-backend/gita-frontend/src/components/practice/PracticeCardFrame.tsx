"use client";

import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

/** Shared page background for Today / Learn / Review. */
export const practiceMainClassName =
  "mx-auto min-h-screen max-w-lg bg-gradient-to-b from-stone-50/80 via-white to-white px-4 pb-12 pt-9 sm:px-5 sm:pt-10";

const shellBase =
  "relative w-full overflow-hidden rounded-xl bg-gradient-to-br from-white via-gold-soft/20 to-white text-left shadow-[0_10px_28px_-18px_rgba(0,0,0,0.14)] ring-1 ring-stone-200/50";

const accentBarGold =
  "pointer-events-none absolute inset-y-3 left-0 w-0.5 rounded-full bg-gradient-to-b from-gold via-gold/75 to-gold/35";

const accentBarSilver =
  "pointer-events-none absolute inset-y-3 left-0 w-0.5 rounded-full bg-gradient-to-b from-slate-500 via-slate-400 to-slate-400/40";

const citationPillGold =
  "absolute right-4 top-4 rounded-full bg-gold-soft/45 px-2 py-0.5 text-[10px] font-medium tabular-nums text-stone-600 ring-1 ring-gold/20";

const citationPillSilver =
  "absolute right-4 top-4 rounded-full bg-slate-100/90 px-2 py-0.5 text-[10px] font-medium tabular-nums text-slate-700 ring-1 ring-slate-300/70";

type Density = "comfortable" | "compact";

const densityPad: Record<Density, string> = {
  comfortable: "px-5 py-7",
  compact: "px-4 py-3.5",
};

type PracticeCardFrameProps = {
  citationKey?: string;
  /** Left accent + citation pill palette. */
  accentTone?: "gold" | "silver";
  density?: Density;
  /** Flip card: renders as `<button>`. */
  interactive?: boolean;
  onClick?: () => void;
  disabled?: boolean;
  /** Static card linking elsewhere (e.g. review list). */
  href?: string;
  children: ReactNode;
  /** One line under content, e.g. “Tap to flip”. */
  footer?: ReactNode;
  bodyClassName?: string;
  bodyMinClassName?: string;
  className?: string;
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children" | "className">;

export function PracticeCardFrame({
  citationKey,
  accentTone = "gold",
  density = "comfortable",
  interactive,
  onClick,
  disabled,
  href,
  children,
  footer,
  bodyClassName,
  bodyMinClassName = "min-h-[200px] sm:min-h-[220px]",
  className,
  type = "button",
  ...buttonRest
}: PracticeCardFrameProps) {
  const pad = densityPad[density];
  const accentBar = accentTone === "silver" ? accentBarSilver : accentBarGold;
  const citationPill = accentTone === "silver" ? citationPillSilver : citationPillGold;
  const linkShell = cn(
    shellBase,
    pad,
    "block shadow-[0_8px_22px_-16px_rgba(0,0,0,0.12)] transition-shadow duration-300 hover:shadow-[0_12px_28px_-14px_rgba(0,0,0,0.14)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--gold)/0.45)] focus-visible:ring-offset-2",
    className,
  );
  const body = (
    <>
      <span className={accentBar} aria-hidden />
      {citationKey ? <span className={citationPill}>{citationKey}</span> : null}
      <div className={cn("relative pl-1 pr-10", bodyMinClassName, bodyClassName)}>{children}</div>
      {footer ? <div className="mt-4 text-center text-[10px] text-stone-500">{footer}</div> : null}
    </>
  );

  if (href) {
    return (
      <Link href={href} className={linkShell}>
        {body}
      </Link>
    );
  }

  if (interactive) {
    const focusRing =
      accentTone === "silver"
        ? "focus-visible:ring-2 focus-visible:ring-slate-400/45 focus-visible:ring-offset-2"
        : "focus-visible:ring-2 focus-visible:ring-[hsl(var(--gold)/0.45)] focus-visible:ring-offset-2";
    return (
      <button
        type={type}
        disabled={disabled}
        onClick={onClick}
        className={cn(
          shellBase,
          "cursor-pointer transition-[box-shadow,transform] duration-300 hover:shadow-[0_14px_32px_-16px_rgba(0,0,0,0.16)] active:scale-[0.99] focus-visible:outline-none",
          focusRing,
          pad,
          className,
        )}
        {...buttonRest}
      >
        {body}
      </button>
    );
  }

  return <div className={cn(shellBase, pad, className)}>{body}</div>;
}
