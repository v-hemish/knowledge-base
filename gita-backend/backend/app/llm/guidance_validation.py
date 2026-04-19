"""
Rule-based validation for LLM guidance explanations (pre–end-user gate).

Targets: very short answers (hard word/sentence caps), narrow therapist-template openings only,
no closing ``See X.Y`` line, distress safety. Used with regenerate-on-fail and a trim pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.llm.output_quality import needs_completion_tail
from app.llm.query_intent import QueryProfile

_GRAMMAR_FRAGMENTS = (
    re.compile(r"\bdiscipline\s+avoid\b", re.I),
    re.compile(r"\bproductive\s+instead\b", re.I),
    re.compile(r"\bthrough\s+self-discipline\s+avoid\b", re.I),
    re.compile(r"\bwhat\s+See\s+\d", re.I),
    re.compile(r"\bconsidering what\s*\.?\s*$", re.I),
)
_DISTRESS_BLUNT = re.compile(
    r"\b(just try harder|pull yourself together|only discipline|weak will|lazy)\b",
    re.I,
)
_ABRUPT_PUNCT_END = re.compile(r"[:;,—]\s*$")
_ENDS_WITH_OPEN_DOUBLE_QUOTE = re.compile(r'"\s*$')
_DISTRESS_STOCK_DISCIPLINE = re.compile(
    r"\b(self-mastery|steady effort|lift yourself|willpower alone|just discipline|"
    r"self-discipline alone|through self-discipline|self-discipline rather|disciplined action)\b",
    re.I,
)
_META_CITATION_LEAK = re.compile(r"\bcitation\s+keys?\b", re.I)
_EMPATHY_MARKERS = re.compile(
    r"\b(kind|gentle|warm|tender|heard|companion|weary|heavy|alone|pace|soft|care|"
    r"human|someone|together|permission|small|quiet)\b",
    re.I,
)
_CLOSING_SEE = re.compile(r"\bSee\s+\d+\.\d+\s*\.?\s*$", re.I)
_MARKDOWNISH = re.compile(r"[#*`_]{2,}|\n\s*[-*]\s+")
# Broken citation stacks the polish pass should fix; reject if they slip through.
_MALFORMED_CITATION_PHRASE = re.compile(
    r"points\s+toward\s+in\s+\d|"
    r"(?:^|[\s.;:!?])'s\s+guidance\s+in\s+\d|"
    r"bhagavad\s+gita\s+'s\s+guidance",
    re.I,
)
# Chapter-only verse references emitted by the model when it truncates after the chapter dot.
# Rejecting these makes ``Bhagavad Gita 2.`` / ``Verse 2.`` / ``Gita 2.`` / ``chapter 2.`` unshippable.
_MALFORMED_VERSE_REFERENCE = re.compile(
    r"\b(?:bhagavad\s+gita|gita|verse|chapter)\s+\d{1,2}\.(?!\d)",
    re.I,
)
# Bare citation lead before a capitalized word after a sentence end (``. 6.5 A concrete…``) —
# the citation is syntactically orphaned; reject so the repair path or regeneration takes over.
_ORPHAN_LEAD_BARE_CITATION = re.compile(
    r"(?:^|[.!?]\s+)\d{1,2}\.\d{1,3}\s+[A-Z]",
)
# Opening-only therapist / worksheet templates. Keep narrow: reject broken tone, not
# every natural scripture phrase (“this passage”, “remember that duty …”, etc.).
_BANNED_OPENING = re.compile(
    r"^\s*(?:"
    r"it sounds like\b|"
    r"when faced with\b|"
    r"i understand(?=\s+(?:that you|your\b|how\s+(?:hard|difficult|heavy)|that this|you are\b))|"
    r"your question\s+(?:is|was|here)\b"
    r")",
    re.I,
)
_TEMPLATE_PHRASES = re.compile(
    r"\b(the bhagavad gita teaches|it can help to remember|it is important to note that|"
    r"this is a reminder that|in conclusion|overall,|fundamentally,)\b",
    re.I,
)
_RUBRIC_STAGE_LEAK = re.compile(
    r"\b(ending with a small concrete next step|use one short reflection question only if)\s*:?\s*",
    re.I,
)
_GENERIC_PAD = re.compile(
    r"\b(it can help|it is important to|remember that you|take comfort in|"
    r"hold space for yourself|you are not alone in feeling)\b",
    re.I,
)
# Default “lecture opener” the product wants to avoid.
_STOCK_VERSE_TEACHES_OPEN = re.compile(
    r"^\s*((verse|bhagavad gita)\s+\d+\.\d+\s+teaches|here\s+\d+\.\d+\s+says|"
    r"this\s+verse\s+teaches|the\s+passage\s+teaches)\b",
    re.I,
)
# Boilerplate reflection / application closers when the line ends in a question.
_STOCK_REFLECTION_QUESTION = re.compile(
    r"\b(reflect on how|how will you start (applying|living)|how will you begin|what will you do to apply|"
    r"take a moment to reflect|have you considered reaching|consider reaching out|why not try to apply|"
    r"can you commit to starting|how can you apply this)\b",
    re.I,
)


@dataclass(frozen=True, slots=True)
class GuidanceValidationResult:
    ok: bool
    reasons: tuple[str, ...]


def strip_trailing_see_citation_line(text: str) -> str:
    """Remove a legacy ``See X.Y.`` closing line if the model still emits it."""
    return _CLOSING_SEE.sub("", (text or "").strip()).strip()


def body_before_trailing_see(text: str) -> str:
    """Body text with optional trailing ``See X.Y`` removed (citation balance)."""
    return strip_trailing_see_citation_line(text)


def primary_citation_label_for(primary_citation_key: str) -> str | None:
    """Structured label to enforce in output (e.g. ``"Bhagavad Gita 2.47"``)."""
    if not primary_citation_key:
        return None
    parts = primary_citation_key.split(".", 1)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return None
    return f"Bhagavad Gita {int(parts[0])}.{int(parts[1])}"


def mentions_exact_primary_label(text: str, *, primary_citation_key: str) -> bool:
    """True if the text contains the exact structured label ``Bhagavad Gita X.Y``.

    This is the strict check used to enforce structured citations. ``mentions_primary_citation``
    remains permissive for regeneration hints, but the final-accept path must see the full
    ``Bhagavad Gita <pk>`` label so UI/downstream consumers never get a bare ``2.47`` token
    or a chapter-only fragment.
    """
    label = primary_citation_label_for(primary_citation_key)
    if not label:
        return True
    return re.search(rf"\b{re.escape(label)}\b", text or "") is not None


def mentions_primary_citation(text: str, *, primary_citation_key: str) -> bool:
    """
    True if the MAIN verse is clearly referenced for validation purposes.

    Accepts canonical ``2.47`` tokens plus common prose variants the model uses
    (e.g. ``Bhagavad Gita 2, 47``, ``Gita 2, 47``, ``chapter 2 … verse 47``) so duty/outcome answers
    are not rejected when the dotted key is omitted.
    """
    if not primary_citation_key:
        return True
    t = text or ""
    if re.search(rf"\b{re.escape(primary_citation_key)}\b", t):
        return True
    parts = primary_citation_key.split(".", 1)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return False
    ch, ve = parts[0].lstrip("0") or "0", parts[1].lstrip("0") or "0"
    ch_n, ve_n = int(ch), int(ve)
    ch_s, ve_s = str(ch_n), str(ve_n)
    if re.search(
        rf"\bBhagavad\s+Gita\s+{re.escape(ch_s)}\s*(?:\.|,)\s*{re.escape(ve_s)}\b",
        t,
        re.I,
    ):
        return True
    if re.search(
        rf"\bVerse\s+{re.escape(ch_s)}\s*(?:\.|,)\s*{re.escape(ve_s)}\b",
        t,
        re.I,
    ):
        return True
    if re.search(
        rf"\bchapter\s+{ch_s}\b[\s\S]{{0,80}}\bverse\s+{ve_s}\b",
        t,
        re.I,
    ):
        return True
    if re.search(
        rf"\bGita\s+{re.escape(ch_s)}\s*(?:\.|,)\s*{re.escape(ve_s)}\b",
        t,
        re.I,
    ):
        return True
    return False


def count_sentences(text: str) -> int:
    """Approximate sentence count; masks citation_key decimals so ``2.47`` does not split."""
    t = (text or "").strip()
    if not t:
        return 0
    masked = re.sub(r"\b\d+\.\d+\b", lambda m: m.group(0).replace(".", "\x00"), t)
    hits = len(re.findall(r"[.!?](?:\s+|$)", masked))
    return max(1, hits)


def citation_mention_counts(body: str, allowed: set[str]) -> dict[str, int]:
    counts = {k: 0 for k in allowed}
    for k in allowed:
        counts[k] = len(re.findall(rf"\b{re.escape(k)}\b", body))
    return counts


def _has_unbalanced_double_quotes(text: str) -> bool:
    return text.count('"') % 2 == 1


def _last_sentence(text: str) -> str:
    """Last sentence-like span for end-of-answer checks (preserves citation_key decimals)."""
    t = (text or "").strip()
    if not t:
        return ""
    masked = re.sub(r"\b\d+\.\d+\b", lambda m: m.group(0).replace(".", "\x00"), t)
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", masked) if p.strip()]
    if not parts:
        return t
    return parts[-1].replace("\x00", ".")


def trim_explanation_to_limits(text: str, *, max_words: int, max_sentences: int) -> str:
    """
    Drop trailing sentences until within word and sentence limits; then hard-truncate words if needed.
    """
    cur = (text or "").strip()
    if not cur:
        return cur
    for _ in range(8):
        ws = cur.split()
        sc = count_sentences(cur)
        if len(ws) <= max_words and sc <= max_sentences:
            return cur
        stripped = re.sub(r"\s*[^.!?]*[.!?]+\s*$", "", cur, count=1, flags=re.S).strip()
        if not stripped or stripped == cur:
            break
        cur = stripped
    ws = cur.split()
    if len(ws) > max_words:
        cur = " ".join(ws[:max_words]).rstrip(",;:")
        if cur and cur[-1] not in ".!?":
            cur += "."
    return cur.strip()


def validate_guidance_explanation(
    text: str,
    *,
    primary_citation_key: str,
    allowed: set[str],
    profile: QueryProfile,
    min_words: int = 20,
    max_words: int = 72,
    max_sentences: int = 3,
) -> GuidanceValidationResult:
    """
    Validate a polished explanation string.

    - Length (min / max words) and max sentences
    - No closing ``See X.Y`` line
    - No banned empathy-template openings
    - No markdown / list markers
    - Truncation / dangling ends; quotes; known grammar artifacts
    - Primary verse must appear by citation_key token
    - Supporting verse must not outweigh primary in mentions
    - Distress-specific tone and support hints
    """
    reasons: list[str] = []
    t = (text or "").strip()
    wc = len(t.split())
    sc = count_sentences(t)

    if wc < min_words:
        reasons.append("too_short")
    if wc > max_words:
        reasons.append("too_long")
    if sc > max_sentences:
        reasons.append("too_many_sentences")

    if _CLOSING_SEE.search(t):
        reasons.append("closing_see_citation_line")

    if _BANNED_OPENING.match(t):
        reasons.append("banned_empathy_opening")

    if _STOCK_VERSE_TEACHES_OPEN.match(t):
        reasons.append("stock_verse_teaches_opening")

    if _MARKDOWNISH.search(t):
        reasons.append("markdown_or_list_artifact")

    if _MALFORMED_CITATION_PHRASE.search(t):
        reasons.append("malformed_citation_phrase")

    if _MALFORMED_VERSE_REFERENCE.search(t):
        reasons.append("malformed_verse_reference")

    if _ORPHAN_LEAD_BARE_CITATION.search(t):
        reasons.append("orphan_leading_bare_citation")

    if _TEMPLATE_PHRASES.search(t):
        reasons.append("template_meta_phrase")

    if _RUBRIC_STAGE_LEAK.search(t):
        reasons.append("template_rubric_leak")

    if len(_GENERIC_PAD.findall(t)) >= 2:
        reasons.append("generic_reassurance_padding")

    if t.rstrip().endswith("?") and _STOCK_REFLECTION_QUESTION.search(_last_sentence(t)):
        reasons.append("stock_reflection_question")

    if needs_completion_tail(t):
        reasons.append("truncation_or_dangling")

    if _ABRUPT_PUNCT_END.search(t):
        reasons.append("abrupt_punctuation_ending")

    if _ENDS_WITH_OPEN_DOUBLE_QUOTE.search(t) or _has_unbalanced_double_quotes(t):
        reasons.append("unfinished_or_unbalanced_quotes")

    if any(pat.search(t) for pat in _GRAMMAR_FRAGMENTS):
        reasons.append("grammar_artifact")

    if _META_CITATION_LEAK.search(t):
        reasons.append("meta_citation_key_leak")

    if primary_citation_key and not mentions_primary_citation(t, primary_citation_key=primary_citation_key):
        reasons.append("missing_primary_citation")

    # Strict structured-label enforcement: the final output must contain the exact label
    # ``Bhagavad Gita <pk>`` (e.g. ``Bhagavad Gita 2.47``). Prose variants (``chapter 2 verse 47``)
    # are accepted by ``missing_primary_citation`` for regeneration hints, but for final accept we
    # require the canonical label so downstream consumers never see a bare ``2.47`` alone.
    if primary_citation_key and not mentions_exact_primary_label(
        t, primary_citation_key=primary_citation_key
    ):
        reasons.append("missing_primary_citation_label")

    body = strip_trailing_see_citation_line(t)
    counts = citation_mention_counts(body, allowed)
    prim = counts.get(primary_citation_key, 0)
    if primary_citation_key and mentions_primary_citation(t, primary_citation_key=primary_citation_key):
        prim = max(prim, 1)
    for k, c in counts.items():
        if k == primary_citation_key:
            continue
        if c > prim + 1 and prim < 2:
            reasons.append(f"body_emphasizes_{k}_over_{primary_citation_key}")

    if profile.distress and _DISTRESS_BLUNT.search(t):
        reasons.append("distress_blamey_tone")

    if profile.distress and len(_DISTRESS_STOCK_DISCIPLINE.findall(t)) >= 3:
        reasons.append("distress_discipline_stock_phrases")

    # Long, emotionally flat answers in distress mode only (avoid rejecting concise grief
    # answers that mention “steady effort” once without a kindness lexicon hit).
    if profile.distress and wc >= 52:
        if len(_DISTRESS_STOCK_DISCIPLINE.findall(t)) >= 1 and len(_EMPATHY_MARKERS.findall(t)) < 1:
            reasons.append("distress_needs_warmer_language")

    return GuidanceValidationResult(ok=len(reasons) == 0, reasons=tuple(reasons))


def build_regeneration_instruction(reasons: tuple[str, ...], *, primary_citation_key: str) -> str:
    """User-turn nudge for a failed draft (append to message list)."""
    joined = "; ".join(reasons) if reasons else "unspecified quality issue"
    return (
        "Your previous draft failed automated checks: "
        f"{joined}. "
        "Rewrite the entire answer in plain text as one calm human reflection. "
        f"Ground the MAIN verse ({primary_citation_key}) within the first two sentences; name it as {primary_citation_key}, "
        f"“Bhagavad Gita {primary_citation_key}”, “Bhagavad Gita {primary_citation_key.split('.')[0]}, {primary_citation_key.split('.')[1]}”, "
        f"or “chapter … verse …”—at least one clear anchor—"
        "never open with “Verse X.Y teaches…” or “Bhagavad Gita X.Y teaches…”. "
        "Vary the opening (e.g. shift in emphasis, clearest guidance, what stands out)—not the same mold as your last try. "
        f"At most 3 short sentences and 72 words. Anchor on {primary_citation_key}; "
        "a second verse, if any, gets at most one short clause. "
        "Prefer a declarative closing sentence or one small concrete step; use a reflection question only if it truly sharpens the thought—not as a habit. "
        "No “See X.Y” line; no markdown; no empathy-template openers. "
        "Use full, grammatical verse references (no orphan “’s guidance in 2.47”; no “points toward in 6.5”; no “2.47 Reflect…” glued). "
        "If the reader may be in distress, stay verse-led and modest—no hotline tone, no discipline-as-main-fix. "
        "Never write the words citation key; never invent verses beyond the blocks you were given."
    )


_SOFT_SENSITIVE_FALLBACK_TEMPLATE = (
    "The clearest guidance in Bhagavad Gita {pk} above is to read that passage on its own terms, slowly. "
    "Give it a few quiet minutes without forcing a mood. "
    "If the weight stays heavy, a trusted person or qualified professional can walk beside you."
)

# Domain-specific deterministic fallback copy keyed by primary verse. Structured citation is
# always ``Bhagavad Gita <pk>`` so validators and UI never see a chapter-only fragment. Each
# string stays within the 20-72 word / 3-sentence validator window and avoids template leakage.
_DOMAIN_SPECIFIC_FALLBACKS: dict[str, str] = {
    "2.47": (
        "Bhagavad Gita 2.47 sets the task plainly: your work is the action itself, not the yield it will bring. "
        "Stay with what is yours to do, and let the result unfold without claiming it in advance. "
        "A small next step is to finish the current task well and stop checking whether it is paying off."
    ),
    "6.5": (
        "Bhagavad Gita 6.5 asks you to lift yourself by your own steady effort rather than let the mind drag you further down. "
        "Treat your own will as an ally, not an enemy, and keep the next rung small enough to actually step onto. "
        "A small next step is to choose one honest action today and complete it without self-blame."
    ),
    "18.66": (
        "Bhagavad Gita 18.66 offers refuge: set down the full weight you are trying to carry alone and entrust the outcome to the divine. "
        "Do the duty in front of you, then release it; the path is guarded by that surrender, not by your grip on results. "
        "A small next step is to name the fear you are holding and place it at the feet of that refuge."
    ),
}


def deterministic_fallback_explanation(
    *,
    primary_citation_key: str,
    distress: bool = False,
    surrender_explicit: bool = False,
) -> str:
    """Return a short safe paragraph when the model repeatedly fails validation.

    Sensitive prompts (distress / grief) get the softer, verse-led template. Non-sensitive
    prompts (e.g. duty_outcomes, discipline) get a verse-specific fallback so the copy stays
    tied to the selected verse rather than a generic "read slowly / trusted person" line.

    The structured primary citation label ``Bhagavad Gita <pk>`` is always present in the
    returned text; no chapter-only fragment or bare digit can appear here.
    """
    pk = (primary_citation_key or "2.47").strip() or "2.47"
    if distress and not surrender_explicit:
        return _SOFT_SENSITIVE_FALLBACK_TEMPLATE.format(pk=pk)
    domain = _DOMAIN_SPECIFIC_FALLBACKS.get(pk)
    if domain:
        return domain
    return _SOFT_SENSITIVE_FALLBACK_TEMPLATE.format(pk=pk)
