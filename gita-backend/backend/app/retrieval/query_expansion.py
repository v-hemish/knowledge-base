"""
Augment user queries for lexical + dense retrieval only.

Modern English (e.g. compulsive habits) often misses classical vocabulary in translations.
Expansion is conservative: extra tokens are plain English and common Gita glosses, never
echoing explicit user wording.
"""

from __future__ import annotations

import re

from app.llm.query_intent import analyze_query

_HEDONIC_OR_COMPULSIVE = re.compile(
    r"\b(?:porn|pornograph|sex\s*addict|addicted\s+to\s+sex|lust|masturbat|"
    r"compulsive\s+sex|cannot\s+stop\s+sex|hooked\s+on\s+porn|sexual\s+compulsion|"
    r"hypersexual|nofap|relapse)\b",
    re.I,
)
_ADDICTION_OR_URGE = re.compile(
    r"\b(?:addict|addiction|addicted|compulsion|compulsive|urge|urges|craving|cravings|"
    r"cannot\s+stop|can'?t\s+stop|out\s+of\s+control)\b",
    re.I,
)


def expanded_retrieval_query(query: str) -> str:
    """
    Return ``query`` plus trailing augmentation tokens for FTS + embedding search.

    The original question is always preserved first so user intent stays primary.
    """
    q = query.strip()
    if not q:
        return q

    extra: list[str] = []
    hedonic = bool(_HEDONIC_OR_COMPULSIVE.search(q))
    urge = bool(_ADDICTION_OR_URGE.search(q))
    prof = analyze_query(q)

    if prof.discipline and not prof.surrender_explicit:
        extra.extend(
            [
                "yoga",
                "practice",
                "mind",
                "steadfast",
                "concentration",
                "restraint",
                "self-mastery",
                "senses",
                "meditation",
                "equanimity",
            ]
        )

    if hedonic:
        extra.extend(
            [
                "senses",
                "sense-objects",
                "objects",
                "attachment",
                "desire",
                "passion",
                "anger",
                "greed",
                "mind",
                "intellect",
                "steady",
                "restraint",
                "discipline",
                "self-mastery",
                "turbulent",
                "longing",
                "withdraw",
                "indriyas",
            ]
        )
    elif urge:
        extra.extend(
            [
                "habit",
                "discipline",
                "mind",
                "steady",
                "attachment",
                "desire",
                "restraint",
                "longing",
                "self-mastery",
            ]
        )

    if not extra:
        return q
    # De-dupe while preserving order (discipline + hedonic can overlap).
    seen: set[str] = set()
    deduped: list[str] = []
    for t in extra:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return f"{q} {' '.join(deduped)}"

