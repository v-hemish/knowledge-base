"use client";

import { Fragment, type ReactNode } from "react";

import { slokaFragmentId } from "./slokaAnchor";

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Split plain text and wrap known `citation_key` tokens as in-page links. */
export function linkCitationsInText(text: string, citationKeys: string[]): ReactNode {
  const keys = [...new Set(citationKeys)].filter(Boolean).sort((a, b) => b.length - a.length);
  if (keys.length === 0) return text;

  const re = new RegExp(`(${keys.map(escapeRegExp).join("|")})`, "g");
  const parts = text.split(re);
  const keySet = new Set(keys);

  return parts.map((part, i) => {
    if (keySet.has(part)) {
      return (
        <a
          key={i}
          href={`#${slokaFragmentId(part)}`}
          className="font-medium text-teal-800 underline decoration-teal-700/40 underline-offset-2 hover:text-teal-950"
        >
          {part}
        </a>
      );
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}
