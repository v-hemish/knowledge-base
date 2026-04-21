"""Editorial placeholder detection (keep in sync with ``gita-frontend`` ``verseQuality.ts``)."""

from __future__ import annotations

_PLACEHOLDER_SUBSTRINGS = (
    "has not translated this verse",
    "many editions of the bhagavad gita do not contain this verse",
    "total number of verses in the bhagavad gita is 701",
)


def is_placeholder_translation(translation: str | None) -> bool:
    if not translation:
        return True
    t = translation.strip()
    if len(t) < 24:
        return True
    lower = t.casefold()
    return any(s in lower for s in _PLACEHOLDER_SUBSTRINGS)
