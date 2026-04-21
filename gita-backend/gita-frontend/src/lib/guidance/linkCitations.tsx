"use client";

import { Fragment, type ReactNode } from "react";

import { slokaFragmentId } from "./slokaAnchor";

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function scrollToVerseAnchor(citationKey: string): void {
  const id = slokaFragmentId(citationKey);
  const el = typeof document !== "undefined" ? document.getElementById(id) : null;
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    window.history.replaceState(null, "", `#${id}`);
    el.classList.remove("verse-card-flash");
    void el.offsetWidth;
    el.classList.add("verse-card-flash");
    window.setTimeout(() => el.classList.remove("verse-card-flash"), 1400);
  }
}

/** Split plain text and wrap known `citation_key` tokens as in-page links (smooth scroll to verse card). */
export function linkCitationsInText(text: string, citationKeys: string[]): ReactNode {
  const keys = [...new Set(citationKeys)].filter(Boolean).sort((a, b) => b.length - a.length);
  if (keys.length === 0) return text;

  const re = new RegExp(`(${keys.map(escapeRegExp).join("|")})`, "g");
  const parts = text.split(re);
  const keySet = new Set(keys);

  return parts.map((part, i) => {
    if (keySet.has(part)) {
      const id = slokaFragmentId(part);
      return (
        <a
          key={i}
          href={`#${id}`}
          className="font-semibold gold-text underline decoration-gold/45 underline-offset-[3px] transition-colors duration-200 hover:text-stone-900 hover:decoration-gold"
          onClick={(e) => {
            e.preventDefault();
            scrollToVerseAnchor(part);
          }}
        >
          {part}
        </a>
      );
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}
