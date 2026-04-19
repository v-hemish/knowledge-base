from __future__ import annotations

from dataclasses import dataclass

from app.models.verse import Verse


@dataclass(frozen=True, slots=True)
class VerseFramingNote:
    citation_key: str
    fit_score: int
    framing: str
    caution: str


_ACTION_TERMS = {
    "work",
    "duty",
    "act",
    "action",
    "results",
    "outcome",
    "outcomes",
    "performance",
    "burnout",
    "burn",
    "control",
}
_SELF_MASTERY_TERMS = {
    "discipline",
    "self",
    "sabotage",
    "depressed",
    "depression",
    "anxious",
    "anxiety",
    "fear",
    "steady",
    "collapse",
    "lift",
    "alone",
}
_SURRENDER_TERMS = {
    "surrender",
    "grace",
    "forgive",
    "forgiveness",
    "sin",
    "devotion",
    "god",
    "krishna",
}


def _tokens(text: str) -> set[str]:
    parts = [p.strip(".,!?;:'\"()[]{}").lower() for p in text.split() if p.strip()]
    toks = set(parts)
    # Simple bigram normalization for common phrases in queries.
    for a, b in zip(parts, parts[1:]):
        if a == "burn" and b == "out":
            toks.add("burnout")
        if a == "self" and b in {"sabotage", "sabotage."}:
            toks.add("sabotage")
    return toks


def _score_for_key(citation_key: str, toks: set[str]) -> tuple[int, str, str]:
    if citation_key == "2.47":
        score = len(_ACTION_TERMS & toks) * 3 + len((_SELF_MASTERY_TERMS & toks)) // 3
        return (
            score,
            "Use for duty and action without attachment to outcomes.",
            "Do not turn this into passivity or emotional dismissal.",
        )
    if citation_key == "6.5":
        score = len(_SELF_MASTERY_TERMS & toks) * 3 + len((_ACTION_TERMS & toks)) // 3
        return (
            score,
            "Use for self-mastery: lift oneself, avoid self-defeat, steady effort.",
            "Do not frame as harsh self-blame or quick cure claims.",
        )
    if citation_key == "18.66":
        score = len(_SURRENDER_TERMS & toks) * 4
        # Penalize emotional pain queries when surrender language is absent.
        if {"depressed", "depression", "anxious", "anxiety", "burnout", "fear"} & toks and score == 0:
            score -= 4
        return (
            score,
            "Use carefully for surrender/trust language only when query supports it.",
            "Do not force this as the main answer for every emotional question.",
        )
    return (0, "Use only if directly relevant to the user question.", "Do not overstate this verse.")


def build_verse_framing(query: str, verses: list[Verse]) -> list[VerseFramingNote]:
    toks = _tokens(query)
    notes: list[VerseFramingNote] = []
    for v in verses:
        score, framing, caution = _score_for_key(v.citation_key, toks)
        notes.append(
            VerseFramingNote(
                citation_key=v.citation_key,
                fit_score=score,
                framing=framing,
                caution=caution,
            )
        )
    return sorted(notes, key=lambda n: n.fit_score, reverse=True)


def reorder_verses_by_fit(query: str, verses: list[Verse]) -> list[Verse]:
    """Lexical-fit ordering only. Prefer :func:`query_intent.rank_verses_by_intent_and_fit` for guidance."""
    if not verses:
        return verses
    notes = build_verse_framing(query, verses)
    rank = {n.citation_key: i for i, n in enumerate(notes)}
    return sorted(verses, key=lambda v: rank.get(v.citation_key, 999))
