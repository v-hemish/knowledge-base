"""
Query intent for retrieval ordering and generation verse subsets.

The MVP corpus may contain only a few verses; intent still diversifies which
verses are emphasized so answers differ meaningfully across question types.

18.66 is reserved for explicit surrender / refuge / trust-in-divine wording—not
general moral conflict, anxiety, or “grace” language alone.

Theme-preference ordering for cards is applied in ``theme_routing.apply_theme_ordered_pins``
after intent+fit ranking (see guidance service).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.llm.verse_framing import build_verse_framing
from app.models.verse import Verse

_TWO_VERSE_REQUEST = re.compile(
    r"\b(?:two|2)\s+vers(?:es|e)|deeper\s+answer|more\s+reflective|pair\s+of\s+verses|"
    r"second\s+verse|another\s+verse|two\s+ślokas|two\s+slokas\b",
    re.I,
)


def wants_two_verse_generation(query: str) -> bool:
    """User explicitly asked for two verses / deeper multi-verse treatment."""
    return bool(_TWO_VERSE_REQUEST.search(query.strip()))


_DISTRESS = re.compile(
    r"\b(depress|depression|depressed|anxiety|anxious|suicid|self[- ]harm|"
    r"panic|trauma|ptsd|hopeless|can'?t cope|cannot cope|want to die|end my life|"
    r"grief|grieving|mourn|emptiness|empty inside|numb)\b",
    re.I,
)
_GRIEF_REGRET = re.compile(
    r"\b(grief|grieving|mourn|after a loss|replay|should have done|bereave|bereaved)\b",
    re.I,
)
_SHAME_PAST = re.compile(
    r"\b(shame|ashamed|regret|guilty|forgive myself|past actions|moral injury)\b",
    re.I,
)
_COMPARISON = re.compile(
    r"\b(compare|comparing|falling behind|behind everyone|others are ahead|envy|jealous|jealousy)\b",
    re.I,
)
_SPIRITUAL_RESTART = re.compile(
    r"\b(spiritually disconnected|begin again|reconnect|lost faith|distant from god|"
    r"how to begin spiritually|start over spiritually|far from god)\b",
    re.I,
)
_BURNOUT = re.compile(
    r"\b(burn(?:t|ed)?\s*out|burnout|overwork|results|outcomes?|obsess|work demands|exhausted)\b",
    re.I,
)
_DISCIPLINE = re.compile(
    r"\b(discipline|disciplined|disciplining|self[- ]sabotag(?:e|ing|ed)?|sabotag(?:e|ing|ed)?|habits?|willpower|consistent|lazy|procrastin|"
    r"delaying|delay\b|putting\s+off|put\s+off)\b",
    re.I,
)
_MORAL = re.compile(
    r"\b(moral|morally|obligation|obligations|duty|duties|wrong choice|choose wrong|"
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
_HEDONIC_COMPULSION = re.compile(
    r"\b(?:porn|pornograph|sex\s*addict|addicted\s+to\s+sex|lust|masturbat|"
    r"compulsive\s+sex|cannot\s+stop\s+sex|hooked\s+on\s+porn|sexual\s+compulsion|"
    r"hypersexual|nofap|relapse)\b",
    re.I,
)
# Work / effort / outcomes / metrics without requiring "burnout" or duty+fruit wording.
_EFFORT_RESULTS = re.compile(
    r"(?:\b(work|working|worker|workers|job|jobs|career|efforts?)\b.{0,90}\b("
    r"results?|outcomes?|success|achievement|metrics|performance|payoff|fruits?|pays?\s+off)\b)|"
    r"(?:\b(results?|outcomes?|success|achievement|metrics|performance|payoff|pays?\s+off)\b.{0,90}\b("
    r"work|working|effort|efforts|job|jobs|career)\b)|"
    r"\b(work hard|feel crushed|chasing success|obsess(?:ing|ed)? over (?:results|metrics|performance)|"
    r"self-worth.{0,40}(?:outcomes?|results?|success)|effort.{0,40}wasted|"
    r"invisible to others|thankless|mechanical and joyless|measuring my value by|"
    r"measur(?:e|ing)\s+my\s+work\s+by|cannot\s+stop\s+measur(?:e|ing))\b",
    re.I,
)
# Outcomes / future uncertainty without explicit "duty" wording (still teaching-verse territory).
_UNCERTAIN_OUTCOME = re.compile(
    r"\b(cannot\s+control|can'?t\s+control|no\s+control|not\s+in\s+my\s+control|"
    r"what\s+happens\s+next|don'?t\s+know\s+what\s+will\s+happen|how\s+it\s+will\s+turn\s+out|"
    r"out\s+of\s+my\s+hands|not\s+up\s+to\s+me|beyond\s+what\s+i\s+can\s+control)\b",
    re.I,
)
_FEAR_OF_FAILURE = re.compile(
    r"\b(afraid\s+to\s+act|scared\s+to\s+try|fear\s+of\s+failing|fear\s+of\s+failure|fear\s+failing|"
    r"afraid\s+of\s+failing|might\s+fail|could\s+fail|"
    r"avoid(?:ing|ed)?\s+action|avoiding\s+action|terrified\s+of\s+failing)\b",
    re.I,
)
_INVISIBLE_EFFORT = re.compile(
    r"\b(thankless|invisible\s+work|unseen\s+work|nobody\s+notices|no\s+one\s+notices|"
    r"my\s+efforts\s+don'?t\s+matter|efforts\s+go\s+unseen)\b",
    re.I,
)
_SELF_WORTH_ACHIEVEMENT = re.compile(
    r"\b("
    r"self[- ]worth.{0,50}(?:achievement|success|grades|titles|performance)|"
    r"(?:achievement|success|grades|titles).{0,40}self[- ]worth|"
    r"only\s+feel\s+worthy\s+when|"
    r"worth\s+depends\s+on\s+(?:how|what)\s+i\s+(?:achieve|perform)"
    r")\b",
    re.I,
)
_GENTLE_DISCIPLINE = re.compile(
    r"\b("
    r"discipline\s+without\s+(?:being\s+)?harsh|gentle\s+discipline|"
    r"disciplin(?:e|ed|ing).{0,40}gently|gently.{0,40}disciplin(?:e|ed|ing)|"
    r"kind(?:er)?\s+to\s+myself.{0,50}discipline|discipline.{0,50}kind(?:er)?\s+to\s+myself|"
    r"not\s+harsh\s+with\s+myself|without\s+becoming\s+harsh|"
    r"self[- ]compassion.{0,40}discipline|discipline.{0,40}self[- ]compassion|"
    r"steadier\s+habits.{0,90}(?:cruel|kind|gentle)|"
    r"disciplin(?:e|ed|ing).{0,90}harsh\s+critic"
    r")\b",
    re.I,
)
_COMFORT_OVER_DUTY = re.compile(
    r"\b("
    r"choos(?:e|ing)\s+comfort\s+over|comfort\s+over\s+what|comfort\s+instead\s+of|"
    r"keep\s+choosing\s+comfort|easy\s+path\s+instead|what\s+i\s+know\s+is\s+right|"
    r"know\s+what'?s\s+right\s+but|short[- ]term\s+comfort|"
    r"instead\s+of\s+doing\s+what\s+i\s+know|what\s+i\s+know\s+i\s+should\s+do"
    r")\b",
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
    hedonic_compulsion: bool
    grief_regret: bool
    shame_past: bool
    comparison: bool
    spiritual_restart: bool
    effort_results: bool
    fear_of_failure: bool
    uncertain_outcome: bool
    invisible_effort: bool
    self_worth_from_achievement: bool
    gentle_discipline: bool
    comfort_over_duty: bool


def analyze_query(query: str) -> QueryProfile:
    q = query.strip()
    surrender_x = bool(_SURRENDER_EXPLICIT.search(q))
    fruit = bool(_ACTION_FRUIT.search(q) and _DUTY_ACT.search(q))
    faith_grace = bool(_FAITH_GRACE.search(q)) and not surrender_x
    shame_past = bool(_SHAME_PAST.search(q)) and not surrender_x
    grief_regret = bool(_GRIEF_REGRET.search(q)) and not surrender_x and not shame_past
    comparison = bool(_COMPARISON.search(q)) and not surrender_x
    spiritual_restart = bool(_SPIRITUAL_RESTART.search(q)) and not surrender_x
    effort_results = bool(_EFFORT_RESULTS.search(q)) and not surrender_x
    action_fruit_hit = bool(_ACTION_FRUIT.search(q))
    uncertain_outcome = (
        bool(_UNCERTAIN_OUTCOME.search(q)) and not surrender_x and not (action_fruit_hit and bool(_DUTY_ACT.search(q)))
    )
    fear_of_failure = bool(_FEAR_OF_FAILURE.search(q)) and not surrender_x
    invisible_effort = bool(_INVISIBLE_EFFORT.search(q)) and not surrender_x
    self_worth_from_achievement = bool(_SELF_WORTH_ACHIEVEMENT.search(q)) and not surrender_x
    gentle_discipline = bool(_GENTLE_DISCIPLINE.search(q)) and not surrender_x
    comfort_over_duty = bool(_COMFORT_OVER_DUTY.search(q)) and not surrender_x
    return QueryProfile(
        distress=bool(_DISTRESS.search(q)),
        burnout=bool(_BURNOUT.search(q)),
        discipline=bool(_DISCIPLINE.search(q)),
        moral_conflict=bool(_MORAL.search(q)),
        surrender_explicit=surrender_x,
        action_without_fruit=fruit and not surrender_x,
        faith_grace_language=faith_grace,
        hedonic_compulsion=bool(_HEDONIC_COMPULSION.search(q)),
        grief_regret=grief_regret,
        shame_past=shame_past,
        comparison=comparison,
        spiritual_restart=spiritual_restart,
        effort_results=effort_results,
        fear_of_failure=fear_of_failure,
        uncertain_outcome=uncertain_outcome,
        invisible_effort=invisible_effort,
        self_worth_from_achievement=self_worth_from_achievement,
        gentle_discipline=gentle_discipline,
        comfort_over_duty=comfort_over_duty,
    )


def intent_boost_for_citation(profile: QueryProfile, citation_key: str) -> int:
    """
    Additive score so retrieval order and generation subsets track question shape.

    2.47: duty / outcomes / burnout / moral conflict / result-obsession.
    6.5: discipline / self-sabotage / inner steadiness (especially when not burnout-led).
    18.66: explicit surrender/refuge/trust-in-divine only.
    """
    effort_adjacent = bool(
        profile.burnout
        or profile.action_without_fruit
        or profile.effort_results
        or profile.uncertain_outcome
        or profile.invisible_effort
        or profile.self_worth_from_achievement
    )
    b = 0
    if citation_key == "2.47":
        if profile.burnout:
            b += 22
        if profile.effort_results and not profile.burnout:
            b += 18
        if profile.moral_conflict:
            b += 20
        if profile.action_without_fruit and not profile.discipline:
            b += 20
        if effort_adjacent and not (profile.burnout or profile.action_without_fruit or profile.effort_results):
            b += 16
        if profile.fear_of_failure:
            b += 18
        if profile.comfort_over_duty:
            b += 16
        if profile.discipline and not profile.burnout:
            b -= 14
        elif profile.discipline:
            b += 2
        if profile.distress:
            b += 10
        if profile.grief_regret:
            b += 14
        if profile.shame_past:
            b += 12
        if profile.comparison:
            b += 10
        if profile.spiritual_restart:
            b += 6
    elif citation_key in ("3.19", "5.12", "3.30", "18.48", "2.40", "2.14", "2.38"):
        if effort_adjacent or profile.comfort_over_duty:
            b += 12
        if profile.moral_conflict:
            b += 6
        if profile.fear_of_failure:
            b += 8
    elif citation_key == "6.5":
        if profile.discipline or profile.gentle_discipline:
            b += 24
        if profile.fear_of_failure:
            b += 14
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
        if profile.grief_regret:
            b += 10
        if profile.shame_past:
            b += 8
        if profile.comparison:
            b += 6
    elif citation_key in ("6.6", "6.26", "6.35", "3.41", "3.43"):
        if profile.discipline or profile.gentle_discipline:
            b += 10
        if profile.gentle_discipline and citation_key in ("6.26", "6.6"):
            b += 8
    elif citation_key == "12.13":
        if profile.gentle_discipline:
            b += 12
    elif citation_key == "3.35" and profile.comfort_over_duty:
        b += 14
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
        if profile.grief_regret and not profile.surrender_explicit:
            b -= 8
        if profile.shame_past:
            b += 4
        if profile.spiritual_restart:
            b += 12
        if not profile.surrender_explicit and any(
            (
                profile.fear_of_failure,
                profile.uncertain_outcome,
                profile.comfort_over_duty,
                profile.invisible_effort,
                profile.self_worth_from_achievement,
                profile.gentle_discipline,
            )
        ):
            b -= 12
    return b


def practical_life_coaching_intent(profile: QueryProfile) -> bool:
    """True for plain-spoken life prompts that should avoid ch.1 narrative / cosmic noise."""
    if profile.surrender_explicit:
        return False
    return bool(
        profile.burnout
        or profile.action_without_fruit
        or profile.effort_results
        or profile.uncertain_outcome
        or profile.invisible_effort
        or profile.self_worth_from_achievement
        or profile.fear_of_failure
        or profile.comfort_over_duty
        or profile.gentle_discipline
        or profile.discipline
        or profile.moral_conflict
        or profile.comparison
        or profile.grief_regret
        or profile.distress
        or profile.shame_past
        or profile.hedonic_compulsion
        or profile.spiritual_restart
        or (profile.faith_grace_language and not profile.surrender_explicit)
    )


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
    Pick 1–2 verses for the LLM from an already-ordered verse list.

    Callers (e.g. guidance) must pass ``verses`` in display order: intent rank, then
    :func:`theme_routing.apply_theme_ordered_pins`, then any final cap.

    18.66 is included only when the question has explicit surrender/refuge/trust language.
    Moral conflict defaults to 2.47 + 6.5, not 18.66.
    """
    if not verses:
        return verses
    profile = analyze_query(query)
    # Caller supplies verses in final display order (rank + theme pins), same as guidance.
    ranked = list(verses)
    by_key = {v.citation_key: v for v in ranked}

    preferred_order: list[str] = []
    if profile.surrender_explicit:
        preferred_order = ["18.66", "2.47"]
    elif profile.burnout or profile.effort_results:
        preferred_order = ["2.47", "6.5"]
    elif profile.action_without_fruit and not profile.discipline:
        preferred_order = ["2.47", "6.5"]
    elif profile.fear_of_failure or profile.uncertain_outcome or profile.invisible_effort or profile.self_worth_from_achievement:
        preferred_order = ["2.47", "6.5"]
    elif profile.comfort_over_duty:
        preferred_order = ["2.47", "3.35"]
    elif profile.gentle_discipline:
        preferred_order = ["6.5", "6.26"]
    elif profile.discipline:
        preferred_order = ["6.5", "2.47"]
    elif profile.moral_conflict:
        preferred_order = ["2.47", "6.5"]

    picked: list[Verse] = []
    seen: set[str] = set()

    if preferred_order:
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

    if wants_two_verse_generation(query) and len(picked) < max_verses:
        from app.llm.theme_routing import theme_pin_order

        for k in theme_pin_order(query):
            if len(picked) >= max_verses:
                break
            if k in seen:
                continue
            v = by_key.get(k)
            if v is None:
                continue
            if k == "18.66" and not profile.surrender_explicit:
                continue
            picked.append(v)
            seen.add(k)

    if not picked:
        picked = [ranked[0]]
    return picked[:max_verses]


def distress_flag(query: str) -> bool:
    """True when extra safety/empathy guidance should apply."""
    return analyze_query(query).distress
