"""
Post-generation heuristics for streamed guidance (completion, citation nudges).

These run server-side after the model stream; they do not replace clinical care or
verse text from the database.
"""

from __future__ import annotations

import re

from app.llm.query_intent import QueryProfile

# Trailing "See 2.47" / "See 6.5." at end of response body.
_TRAILING_SEE = re.compile(r"See\s+(\d+\.\d+)\s*\.?\s*$", re.IGNORECASE)


def needs_completion_tail(text: str) -> bool:
    """
    True when the explanation likely ended mid-thought (truncation, hard cap, etc.).

    Conservative: prefer a short completion sentence over leaving a broken tail.
    """
    t = (text or "").strip()
    if not t:
        return False
    last = t[-1]
    if last not in ".!?":
        return True
    # Reflection questions are treated as intentionally complete for short guidance.
    if last == "?":
        return False
    # Strip final punctuation for dangling-phrase checks.
    core = t[:-1].rstrip().lower()
    if not core:
        return False
    dangling = (
        " and",
        " or",
        " the",
        " a",
        " an",
        " your",
        " my",
        " our",
        " their",
        " that",
        " which",
        " to",
        " for",
        " with",
        " of",
        " could",
        " might",
        " brings",
        " managing",
        " areas",
        " toward",
        " where",
        " when",
        " how",
        " feel",
        " requires",
    )
    return any(core.endswith(d.strip()) for d in dangling)


def trailing_see_citation_key(text: str) -> str | None:
    """Return citation_key from a trailing 'See X.Y' if present."""
    m = _TRAILING_SEE.search((text or "").strip())
    return m.group(1) if m else None


def citation_clarification_suffix(
    text: str,
    *,
    primary: str,
    allowed: set[str],
    profile: QueryProfile,
) -> str | None:
    """
    If the model ended with ``See …`` that conflicts with intent-primary, append one
    clarifying sentence (allowed keys only; never invent a verse).
    """
    if primary not in allowed:
        return None
    tail = trailing_see_citation_key(text)
    if tail is None or tail == primary:
        return None
    if tail not in allowed:
        return None

    if profile.burnout and primary == "2.47" and tail == "6.5":
        return f" For obsession with outcomes and depletion, lean especially on {primary}."
    if profile.moral_conflict and primary == "2.47" and tail == "6.5":
        return f" When duties pull in different directions, center {primary} first."
    if profile.discipline and primary == "6.5" and tail == "2.47":
        return f" For steadying self-defeating cycles, weight {primary} ahead of {tail}."
    if profile.surrender_explicit and primary == "18.66" and tail != "18.66":
        return f" For surrender and refuge, {primary} speaks most directly here."
    return None
