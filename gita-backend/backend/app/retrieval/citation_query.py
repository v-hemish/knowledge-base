"""Detect explicit chapter.verse citation in short retrieve queries (practice UI, deep links)."""

from __future__ import annotations

import re

# "Bhagavad Gita 2.47" / "bhagavad gita 18.66" (frontend practice fetch)
_RE_BG_CITATION = re.compile(
    r"\bBhagavad\s+Gita\s+([1-9]|1[0-8])\.(\d{1,3})\b",
    re.IGNORECASE,
)
# Bare citation only
_RE_STANDALONE_CITATION = re.compile(r"^\s*([1-9]|1[0-8])\.(\d{1,3})\s*$")


def citation_key_from_retrieval_query(query: str) -> str | None:
    """
    Return canonical ``chapter.verse`` if the query is clearly asking for one verse
    by address (not a thematic question that merely mentions a number).
    """
    q = query.strip()
    if not q:
        return None
    m0 = _RE_STANDALONE_CITATION.match(q)
    if m0:
        ch, vs = int(m0.group(1)), int(m0.group(2))
        return _validated_citation_key(ch, vs)
    m = _RE_BG_CITATION.search(q)
    if m is None:
        return None
    ch, vs = int(m.group(1)), int(m.group(2))
    return _validated_citation_key(ch, vs)


def _validated_citation_key(chapter: int, verse: int) -> str | None:
    if chapter < 1 or chapter > 18 or verse < 1 or verse > 300:
        return None
    return f"{chapter}.{verse}"
