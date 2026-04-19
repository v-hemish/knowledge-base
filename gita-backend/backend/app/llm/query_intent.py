"""
Query intent for retrieval ordering and generation verse subsets.

The MVP corpus may contain only a few verses; intent still diversifies which
verses are emphasized so answers differ meaningfully across question types.

18.66 is reserved for explicit surrender / refuge / trust-in-divine wording—not
general moral conflict, anxiety, or “grace” language alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.llm.verse_framing import build_verse_framing
from app.models.verse import Verse


_DISTRESS = re.compile(
    r"\b(depress|depression|depressed|anxiety|anxious|suicid|self[- ]harm|"
    r"panic|trauma|ptsd|hopeless|can'?t cope|cannot cope|want to die|end my life|"
    r"grief|grieving|mourn|emptiness|empty inside|numb)\b",
    re.I,
)
_BURNOUT = re.compile(
    r"\b(burn\s*out|burnout|overwork|results|outcomes?|obsess|work demands|exhausted)\b",
    re.I,
)
_DISCIPLINE = re.compile(
    r"\b(discipline|self[- ]sabotage|habit|willpower|consistent|lazy|procrastin)\b",
    re.I,
)
_MORAL = re.compile(
    r"\b(moral|obligation|obligations|duty|duties|wrong choice|choose wrong|"
    r"tug[- ]of[- ]war|competing|dilemma)\b",
    re.I,
)
# Only these trigger 18.66 as a primary routing signal (theological “surrender” sense).
_SURRENDER_EXPLICIT = re.compile(
    r"\b(surrender(ing|ed)?|take refuge|refuge in(\s+god|\s+the divine|\s+krishna)?|"
    r"trust in (god|the divine|krishna|allah)|sarana|sharana)\b",
    re.I,
)
# Grace / faith / helplessness without the above—tone hints only, not 18.66 drivers.
_FAITH_GRACE = re.compile(r"\b(grace|faith|helplessness|pray|prayer)\b", re.I)
_ACTION_FRUIT = re.compile(
    r"\b(cannot control|can't control|no control|not control how|how it will turn out|"
    r"turn out|out of my control|outcomes?|results?\b|fruit of|fruits of|what happens)\b",
    re.I,
)
_DUTY_ACT = re.compile(
    r"\b(duty|duties|must act|have to act|right action|need to act|i must|have to do)\b",
    re.I,
)


@dataclass(frozen=True, slots=True)
class QueryProfile:
    """Lightweight flags derived from the user question (heuristics only)."""

    distress: bool
    burnout: bool
    discipline: bool
    moral_conflict: bool
    surrender_explicit: bool
    action_without_fruit: bool
    faith_grace_language: bool


def analyze_query(query: str) -> QueryProfile:
    q = query.strip()
    surrender_x = bool(_SURRENDER_EXPLICIT.search(q))
    fruit = bool(_ACTION_FRUIT.search(q) and _DUTY_ACT.search(q))
    faith_grace = bool(_FAITH_GRACE.search(q)) and not surrender_x
    return QueryProfile(
        distress=bool(_DISTRESS.search(q)),
        burnout=bool(_BURNOUT.search(q)),
        discipline=bool(_DISCIPLINE.search(q)),
        moral_conflict=bool(_MORAL.search(q)),
        surrender_explicit=surrender_x,
        action_without_fruit=fruit and not surrender_x,
        faith_grace_language=faith_grace,
    )


def intent_boost_for_citation(profile: QueryProfile, citation_key: str) -> int:
    """
    Additive score so retrieval order and generation subsets track question shape.

    2.47: duty / outcomes / burnout / moral conflict / result-obsession.
    6.5: discipline / self-sabotage / inner steadiness (especially when not burnout-led).
    18.66: explicit surrender/refuge/trust-in-divine only.
    """
    b = 0
    if citation_key == "2.47":
        if profile.burnout:
            b += 22
        if profile.moral_conflict:
            b += 20
        if profile.action_without_fruit and not profile.discipline:
            b += 20
        if profile.discipline and not profile.burnout:
            b -= 14
        elif profile.discipline:
            b += 2
        if profile.distress:
            b += 10
    elif citation_key == "6.5":
        if profile.discipline:
            b += 24
        if profile.distress and profile.discipline:
            b += 8
        if profile.distress and not profile.discipline:
            b -= 12
        if profile.burnout:
            b += 1
        if profile.moral_conflict:
            b += 6
        if profile.action_without_fruit and not profile.discipline:
            b -= 12
    elif citation_key == "18.66":
        if profile.surrender_explicit:
            b += 30
        if profile.moral_conflict and not profile.surrender_explicit:
            b -= 42
        if profile.distress and not profile.surrender_explicit:
            b -= 14
        if profile.burnout and not profile.surrender_explicit:
            b -= 10
        if profile.discipline and not profile.surrender_explicit:
            b -= 36
    return b


def rank_verses_by_intent_and_fit(query: str, verses: list[Verse]) -> list[Verse]:
    """Order verses by combined framing fit + intent boost (higher first)."""
    if not verses:
        return verses
    profile = analyze_query(query)
    notes = build_verse_framing(query, verses)
    base = {n.citation_key: n.fit_score for n in notes}

    def total(v: Verse) -> int:
        return base.get(v.citation_key, 0) + intent_boost_for_citation(profile, v.citation_key)

    return sorted(verses, key=lambda v: (-total(v), v.citation_key))


def select_verses_for_generation(
    query: str,
    verses: list[Verse],
    *,
    max_verses: int = 2,
) -> list[Verse]:
    """
    Pick 1–2 verses for the LLM: best distinct keys after intent+fit ranking.

    18.66 is included only when the question has explicit surrender/refuge/trust language.
    Moral conflict defaults to 2.47 + 6.5, not 18.66.
    """
    if not verses:
        return verses
    ranked = rank_verses_by_intent_and_fit(query, verses)
    profile = analyze_query(query)

    picked: list[Verse] = []
    seen: set[str] = set()

    preferred_order: list[str] = []
    if profile.surrender_explicit:
        preferred_order = ["18.66", "2.47"]
    elif profile.burnout:
        preferred_order = ["2.47", "6.5"]
    elif profile.action_without_fruit and not profile.discipline:
        preferred_order = ["2.47", "6.5"]
    elif profile.discipline:
        preferred_order = ["6.5", "2.47"]
    elif profile.moral_conflict:
        preferred_order = ["2.47", "6.5"]

    if preferred_order:
        by_key = {v.citation_key: v for v in ranked}
        for k in preferred_order:
            if k in by_key and k not in seen and len(picked) < max_verses:
                picked.append(by_key[k])
                seen.add(k)

    for v in ranked:
        if len(picked) >= max_verses:
            break
        if v.citation_key in seen:
            continue
        if v.citation_key == "18.66" and not profile.surrender_explicit:
            continue
        picked.append(v)
        seen.add(v.citation_key)

    if not picked:
        picked = [ranked[0]]
    return picked[:max_verses]


def distress_flag(query: str) -> bool:
    """True when extra safety/empathy guidance should apply."""
    return analyze_query(query).distress
