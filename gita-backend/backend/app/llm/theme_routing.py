"""
Explicit theme pins for verse ordering after retrieval + intent scoring.

Principles:
- Prefer strongest canonical fits over novelty.
- Never invent retrieval hits; only reorder verses already retrieved.
- Keep routing conservative for emotionally sensitive prompts.
- Support optional 2-verse generation by pinning a primary and support family.
"""

from __future__ import annotations

import sqlite3

from app.db.verses_repo import fetch_verses_by_citation_keys
from app.llm.query_intent import QueryProfile, analyze_query, practical_life_coaching_intent
from app.models.verse import Verse

# -----------------------------
# Canonical theme families
# -----------------------------
# Ordered from clearest / safest fit to broader supporting fits.

# Action without attachment to results, effort vs fruits, performance obsession.
_EFFORT_FRUIT: tuple[str, ...] = (
    "2.47",
    "3.19",
    "5.12",
    "3.30",
    "18.48",
    "2.40",
    "2.14",
    "2.38",
)

# Fear of failing / avoidance of right action; still teaching-verse territory.
_FEAR_FAILURE_ACT: tuple[str, ...] = (
    "2.47",
    "3.30",
    "18.48",
    "6.5",
    "2.40",
    "3.19",
    "5.12",
)

# Comfort-seeking vs integrity (“I know what is right”).
_COMFORT_DUTY: tuple[str, ...] = (
    "2.47",
    "3.35",
    "6.5",
    "3.43",
    "18.48",
    "3.30",
    "3.41",
)

# Discipline without self-attack; steadiness + gentleness.
_GENTLE_DISCIPLINE: tuple[str, ...] = (
    "6.5",
    "6.26",
    "6.6",
    "12.13",
    "3.41",
    "3.43",
    "17.3",
    "18.42",
)

# Discipline, self-sabotage, steadiness of mind, habit formation.
_DISCIPLINE: tuple[str, ...] = (
    "6.5",
    "6.6",
    "6.26",
    "6.35",
    "3.41",
    "3.43",
    "17.3",
    "18.42",
)

# Explicit surrender, refuge, trust in God, fear relieved by refuge.
_SURRENDER: tuple[str, ...] = (
    "18.66",  # surrender to Me, do not fear
    "18.62",  # take refuge with all being
    "18.61",  # Lord seated in heart
    "9.22",  # preserve what devotee lacks
    "12.6",  # those who worship with devotion
    "12.7",  # I deliver them from ocean of death
    "15.4",  # seek refuge in the primal person
)

# Moral conflict, competing obligations, integrity, difficult choices.
_MORAL: tuple[str, ...] = (
    "2.47",  # do your duty, not outcomes
    "3.35",  # better one’s own duty
    "18.63",  # reflect fully and act as you think right
    "18.48",  # duty may be imperfect but should not be abandoned
    "6.5",  # do not collapse into self-defeat
    "2.7",  # Arjuna’s bewilderment, asks for guidance
)

# Grief, regret, replaying the past, guilt after loss.
_GRIEF: tuple[str, ...] = (
    "2.13",  # embodied change / continuity
    "2.14",  # passing pain and pleasure
    "2.27",  # death is certain for the born
    "2.47",  # act, don’t cling to outcomes
    "5.20",  # not elated or broken by events
    "6.5",  # don’t sink further inwardly
)

# Distress, emptiness, depression-adjacent but not explicit self-harm.
_DISTRESS: tuple[str, ...] = (
    "6.5",  # self as friend/enemy, uplift gently
    "2.14",  # distress is passing, tolerate softly
    "12.12",  # peace follows renunciation of fruits
    "18.54",  # serene self, no lamentation
    "15.15",  # divine presence in the heart
    "2.47",  # act without fruit fixation
)

# Hedonic compulsion, craving, anger, indulgence, addiction-like loops.
_HEDONIC: tuple[str, ...] = (
    "2.62",
    "2.63",
    "2.64",
    "3.37",
    "3.41",
    "3.43",
    "16.21",
)

# Shame, moral injury, self-forgiveness, recovery after wrongdoing.
_SHAME_REPAIR: tuple[str, ...] = (
    "2.47",
    "3.30",
    "6.5",
    "12.13",
    "18.66",
)

# Comparison, envy, feeling behind, measuring self against others.
_COMPARISON: tuple[str, ...] = (
    "3.35",
    "2.47",
    "5.12",
    "6.5",
    "12.15",
)

# Spiritual disconnection / how to begin again.
_SPIRITUAL_RESTART: tuple[str, ...] = (
    "18.66",
    "18.62",
    "12.6",
    "12.7",
    "15.15",
    "10.10",
    "10.11",
)

# Surfaces for consistency tests and tooling.
CANONICAL_EFFORT_FAMILY: frozenset[str] = frozenset(_EFFORT_FRUIT)
CANONICAL_DISCIPLINE_FAMILY: frozenset[str] = frozenset(_DISCIPLINE)
CANONICAL_FEAR_FAILURE_FAMILY: frozenset[str] = frozenset(_FEAR_FAILURE_ACT)
CANONICAL_COMFORT_DUTY_FAMILY: frozenset[str] = frozenset(_COMFORT_DUTY)
CANONICAL_GENTLE_DISCIPLINE_FAMILY: frozenset[str] = frozenset(_GENTLE_DISCIPLINE)

# -----------------------------
# Optional exclusions (theme-specific)
# -----------------------------
_AVOID_FOR_DISTRESS = {
    "16.9",
    "11.20",
    "11.42",
    "11.45",
    "10.42",
}

_AVOID_FOR_GRIEF = {
    "10.42",
    "11.44",
}

_AVOID_FOR_BURNOUT = {
    "11.42",
    "10.42",
    "4.7",
}

_AVOID_FOR_DISCIPLINE = {
    "10.42",
    "11.20",
}

# Verses that rarely help plain-spoken life problems; demote unless surrender-only.
_WEAK_PRACTICAL_VERSES: frozenset[str] = frozenset(
    {
        "1.28",
        "1.29",
        "1.30",
        "1.31",
        "10.36",
        "10.42",
        "14.16",
        "16.11",
    }
)

# Cosmic / theophany listing verses that often lexically hit “fear / act / discipline” English.
_COSMIC_PRACTICAL_DEMOTE: frozenset[str] = frozenset(
    {
        "10.2",
        "10.6",
        "10.17",
        "10.19",
        "10.20",
        "10.21",
        "10.22",
        "10.24",
        "10.33",
        "11.4",
        "11.20",
        "12.11",
    }
)


def _demote_weak_practical_verses(profile: QueryProfile) -> bool:
    """When True, push common Arjuna-narrative / cosmic hits to the tail."""
    return practical_life_coaching_intent(profile)


def _pin_order_for_profile(profile: QueryProfile) -> tuple[str, ...] | None:
    if profile.surrender_explicit:
        return _SURRENDER
    if profile.moral_conflict:
        return _MORAL
    if profile.comfort_over_duty:
        return _COMFORT_DUTY
    if profile.fear_of_failure:
        return _FEAR_FAILURE_ACT
    if (
        profile.burnout
        or profile.action_without_fruit
        or profile.effort_results
        or profile.uncertain_outcome
        or profile.invisible_effort
        or profile.self_worth_from_achievement
    ):
        return _EFFORT_FRUIT
    if profile.gentle_discipline:
        return _GENTLE_DISCIPLINE
    if profile.discipline:
        return _DISCIPLINE
    if profile.grief_regret:
        return _GRIEF
    if profile.distress:
        return _DISTRESS
    if profile.hedonic_compulsion:
        return _HEDONIC
    if profile.shame_past:
        return _SHAME_REPAIR
    if profile.comparison:
        return _COMPARISON
    if profile.spiritual_restart:
        return _SPIRITUAL_RESTART
    return None


def _avoid_set_for_profile(profile: QueryProfile) -> set[str]:
    out: set[str] = set()
    if profile.distress:
        out |= _AVOID_FOR_DISTRESS
    if profile.grief_regret:
        out |= _AVOID_FOR_GRIEF
    if (
        profile.burnout
        or profile.action_without_fruit
        or profile.effort_results
        or profile.uncertain_outcome
        or profile.invisible_effort
        or profile.self_worth_from_achievement
    ):
        out |= _AVOID_FOR_BURNOUT
    if profile.discipline or profile.gentle_discipline:
        out |= _AVOID_FOR_DISCIPLINE
    if profile.fear_of_failure or profile.comfort_over_duty:
        out |= _COSMIC_PRACTICAL_DEMOTE
    if _demote_weak_practical_verses(profile):
        out |= set(_WEAK_PRACTICAL_VERSES)
        out |= set(_COSMIC_PRACTICAL_DEMOTE)
    return out


def theme_pin_order(query: str) -> tuple[str, ...]:
    """Ordered citation keys for the active theme (empty if none)."""
    return _pin_order_for_profile(analyze_query(query)) or ()


def prepend_theme_canonical_verses(
    conn: sqlite3.Connection,
    query: str,
    verses: list[Verse],
    *,
    max_add: int = 10,
) -> list[Verse]:
    """
    Ensure active theme pin verses exist in the candidate pool.

    Rows are still loaded from the database (same source as FTS hits); this only
    repairs recall gaps so intent ranking and ``apply_theme_ordered_pins`` can run.
    """
    pins = theme_pin_order(query)
    if not pins:
        return verses
    have = {v.citation_key for v in verses}
    missing = [k for k in pins if k not in have][:max_add]
    if not missing:
        return verses
    fetched = fetch_verses_by_citation_keys(conn, missing)
    prefix = [fetched[k] for k in missing if k in fetched]
    if not prefix:
        return verses
    pref_keys = {v.citation_key for v in prefix}
    rest = [v for v in verses if v.citation_key not in pref_keys]
    return prefix + rest


def _citation_demoted_for_practical(profile: QueryProfile, avoid: set[str], citation_key: str) -> bool:
    if citation_key in avoid:
        return True
    if practical_life_coaching_intent(profile) and citation_key.startswith("1."):
        return True
    return False


def apply_theme_ordered_pins(query: str, verses: list[Verse]) -> list[Verse]:
    """
    Move theme-canonical verses (when present) to the front, in fixed pin order.
    Remaining verses keep their relative order after the pinned prefix.
    Also demote weak-fit verses for certain sensitive themes.
    """
    if not verses:
        return verses

    profile = analyze_query(query)
    pins = _pin_order_for_profile(profile)
    avoid = _avoid_set_for_profile(profile)

    # Stable partition: first candidates not demoted, then demoted (weak / ch.1 narrative / cosmic).
    filtered_first = [v for v in verses if not _citation_demoted_for_practical(profile, avoid, v.citation_key)]
    filtered_last = [v for v in verses if _citation_demoted_for_practical(profile, avoid, v.citation_key)]
    verses = filtered_first + filtered_last

    if not pins:
        return verses

    by_key = {v.citation_key: v for v in verses}
    out: list[Verse] = []
    seen: set[str] = set()

    for k in pins:
        v = by_key.get(k)
        if v is not None and k not in seen:
            out.append(v)
            seen.add(k)

    for v in verses:
        if v.citation_key not in seen:
            out.append(v)
            seen.add(v.citation_key)

    return out
