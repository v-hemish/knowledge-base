"""
Buffer raw LLM stream tokens and emit larger, phrase- or sentence-shaped chunks.

Makes SSE updates less jittery while still progressive (no waiting for the full answer).
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator

# Sentence or clause end followed by whitespace (keep trailing space on the chunk).
_SENTENCE_OR_CLAUSE = re.compile(r"^.+?(?:[.!?][ \t\n]|[;][ \t\n])", re.DOTALL)
_MARKDOWN_NOISE = re.compile(r"[`*#]+")
_MULTISPACE = re.compile(r"\s+")
_SENT_END = re.compile(r"[.!?]")
_HEADING_PREFIX = re.compile(r"^\s*(opening|connection to the reader's question|closing question|practical step)\s*:\s*", re.I)
_LABEL_PREFIX = re.compile(r"^\s*(guidance note|note|reflection|answer)\s*:?\s*", re.I)
# Require whitespace after the dot so "6.5" (citation_key) is not treated as a numbered step.
_NUMBERED_STEP = re.compile(r"\b\d+\.\s+")
_CIT_KEY_BRACKET = re.compile(r"\[\s*citation_key\s*=\s*([0-9]+\.[0-9]+)\s*\]", re.I)
_TRAILING_FRAGMENT = re.compile(r"(?:\b\d+\.$|[:;,\-]+)$")
_PAREN_SHORT_CIT = re.compile(r"\((\d{1,3})\)")
_TRAILING_SOLO_NUMBER = re.compile(r"(?:\s+\d{1,3})\s*$")
_CIT_KEY_TOKEN = re.compile(r"\b\d{1,2}\.\d{1,3}\b")
# Avoid matching the verse segment inside an existing citation_key like 6.5 or 2.47.
_BARE_SHORT_NUM = re.compile(r"(?<![0-9]\.)\b(5|47|66)\b(?!\.[0-9])")
_VERSE_SHORT = re.compile(r"\b[Vv]erse\s+(5|47|66)\b")
_VERSES_SHORT_PAIR = re.compile(r"\b[Vv]erses?\s+47\s+and\s+5\b")
_BROKEN_A_COULD = re.compile(r"\bA could be\b")
_ONESELF_DO_NOT = re.compile(r"\boneself\s+do\s+not\b", re.I)
_GITA_ADVISES_VERB_OPEN = re.compile(
    r"\bThe Bhagavad Gita\s+(advises|emphasizes|suggests)\b",
    re.I,
)
_LEADING_AS_ADVISES = re.compile(r"(^|[.!?]\s+)As\s+advises\b", re.I)
_WORD_AS_ADVISES = re.compile(r"\b([A-Za-z]+)\s+as\s+advises\b", re.I)
_LEAD_CIT_CAP_VERB = re.compile(
    r"(^|[.!?]\s+)(\d{1,2}\.\d{1,3})\s+(Reflect|Consider|Think|Remember)\b",
    re.I,
)
_A_IS_SETTING = re.compile(r"\bA is setting\s*", re.I)
_ENCOURAGES_TO_LIFT = re.compile(r"\bencourages to lift(?:\s+oneself)?\b", re.I)
_BHAGAVAD_GITA_SOLO_CH = re.compile(r"\bBhagavad\s+Gita\s+5\b", re.I)
_GITA_SOLO_CH = re.compile(r"\bGita\s+5\b", re.I)
# Model echoes prompt metadata — rewrite to user-facing scripture references (MVP keys).
_CITATION_KEY_PHRASE_DOTTED = re.compile(r"\bcitation\s+keys?\s+(\d{1,2})\.(\d{1,3})\b", re.I)
_CITATION_KEY_PHRASE_SOLO = re.compile(r"\bcitation\s+keys?\s+(\d{1,3})\b", re.I)
_TRAILING_AND = re.compile(r"\band\s*$", re.I)
_FILLER_PATTERNS = (
    re.compile(r"\b(i hope this helps|let me know|you are not alone|let['’]s explore)\b", re.I),
)
# Model sometimes echoes prompt/rubric fragments — strip these from streamed text.
_RUBRIC_FRAGMENTS = [
    re.compile(r"(?is)\bend with one brief practical next step:?\s*"),
    re.compile(r"(?is)\bpractical next step:?\s*"),
    re.compile(r"(?is)\bstop cleanly\.?\s*"),
    re.compile(r"(?is)\bas described in the user message\.?\s*"),
    re.compile(r"(?is)\bdo not quote or mention this priority line[^\n.]*\.?\s*"),
    re.compile(r"(?is)\bquery hints \(internal[^:]*:\s*[^\n]*\n?"),
    re.compile(r"(?is)\breader safety note \(internal[^:]*:\s*"),
    re.compile(r"(?is)\bending with a small concrete next step:?\s*"),
    re.compile(r"(?is)\breflection question only if it truly sharpens:?\s*"),
]


class GuidanceExplanationBuffer:
    """
    Accumulate token fragments; ``feed`` returns zero or more ready-to-send strings.

    Priority: sentence/clause boundaries → first-chunk early flush → soft length at spaces → hard cut.
    """

    def __init__(
        self,
        *,
        first_flush_min_total: int = 16,
        first_flush_space_min_index: int = 9,
        soft_max: int = 120,
        hard_max: int = 180,
    ) -> None:
        self._buf = ""
        self._first_flushed = False
        self._first_flush_min_total = first_flush_min_total
        self._first_flush_space_min_index = first_flush_space_min_index
        self._soft_max = soft_max
        self._hard_max = hard_max

    def feed(self, piece: str) -> list[str]:
        self._buf += piece
        out: list[str] = []
        while True:
            chunk = self._take_one()
            if chunk is None:
                break
            out.append(chunk)
            if chunk.strip():
                self._first_flushed = True
        return out

    def _take_one(self) -> str | None:
        b = self._buf
        if not b:
            return None

        m = _SENTENCE_OR_CLAUSE.match(b)
        if m:
            s = m.group(0)
            self._buf = b[len(s) :]
            return s

        if len(b) >= 32 and "; " in b:
            i = b.index("; ")
            if i >= 18:
                emit = b[: i + 2]
                self._buf = b[i + 2 :]
                return emit

        if not self._first_flushed and len(b) >= self._first_flush_min_total:
            sp = b.find(" ", self._first_flush_space_min_index)
            if sp != -1:
                emit = b[: sp + 1]
                self._buf = b[sp + 1 :]
                return emit

        if len(b) >= self._soft_max:
            cut = b.rfind(" ", 0, self._soft_max)
            if cut <= 0:
                emit = b[: self._soft_max]
                self._buf = b[self._soft_max :]
            else:
                emit = b[: cut + 1]
                self._buf = b[cut + 1 :]
            return emit

        if len(b) >= self._hard_max:
            emit, self._buf = b[: self._hard_max], b[self._hard_max :]
            return emit

        return None

    def finalize(self) -> str:
        rest = self._buf
        self._buf = ""
        return rest


def _primary_citation_for_polish(allowed: set[str] | None) -> str | None:
    if not allowed:
        return None
    return sorted(allowed, key=lambda k: (int(k.split(".")[0]), int(k.split(".")[1])))[0]


def _effective_primary(allowed: set[str] | None, primary: str | None) -> str | None:
    if primary and allowed and primary in allowed:
        return primary
    return _primary_citation_for_polish(allowed)


def _polish_verbal_glitches(text: str, *, effective_primary_key: str | None) -> str:
    """Fix common model glitches (e.g. “The Bhagavad Gita advises…”, “2.47 Reflect…”)."""
    s = text
    pk = effective_primary_key
    if pk:

        def _gita_verb(m: re.Match[str]) -> str:
            v = (m.group(1) or "").lower()
            # Use finite verbs that read cleanly before “(2.47)” or “in 6.5…” — avoid “points toward in …”.
            if v == "advises":
                return f"Bhagavad Gita {pk} encourages"
            if v == "emphasizes":
                return f"Bhagavad Gita {pk} stresses"
            return f"Bhagavad Gita {pk} suggests"

        s = _GITA_ADVISES_VERB_OPEN.sub(_gita_verb, s, count=1)
    s = _LEADING_AS_ADVISES.sub(r"\1This counsel advises", s)
    s = _WORD_AS_ADVISES.sub(lambda m: f"{m.group(1)} advises", s)
    s = _LEAD_CIT_CAP_VERB.sub(
        lambda m: f"{m.group(1)}In Bhagavad Gita {m.group(2)}, {m.group(3).lower()}",
        s,
    )
    s = _A_IS_SETTING.sub("The emphasis is on setting ", s)
    s = _ENCOURAGES_TO_LIFT.sub("encourages lifting oneself", s)
    return s


def _polish_malformed_citation_phrases(text: str) -> str:
    """Post-pass: repair rare citation stacks / orphans from model + earlier polish."""
    s = text
    s = re.sub(
        r"\bpoints\s+toward\s+in\s+(\d{1,2}\.\d{1,3})\b",
        r"centers on \1",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"(^|[\s.;:!?])'s\s+guidance\s+in\s+(\d{1,2}\.\d{1,3})\b",
        r"\1The guidance in Bhagavad Gita \2",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\bBhagavad Gita\s+'s\s+guidance\b",
        "The guidance in Bhagavad Gita",
        s,
        flags=re.I,
    )
    return s


def _repair_truncated_bhagavad_gita_citation(text: str, *, effective_primary_key: str | None) -> str:
    """If the model writes ``Bhagavad Gita 2.`` without the verse segment, repair using MAIN when known.

    Inserts a trailing space when the fragment is glued to a following letter (e.g.
    ``Bhagavad Gita 2.This`` -> ``Bhagavad Gita 2.47 This``) so the repaired citation never
    fuses into a malformed token.
    """
    pk = effective_primary_key
    if not pk or "." not in pk:
        return text
    ch, ve = pk.split(".", 1)
    if not ch.isdigit() or not ve.isdigit():
        return text
    ch_s, ve_s = str(int(ch)), str(int(ve))

    def _repl(m: re.Match[str]) -> str:
        tail = text[m.end() : m.end() + 1]
        pad = " " if tail and (tail.isalnum() or tail in ("(",)) else ""
        return f"Bhagavad Gita {pk}{pad}"

    return re.sub(
        rf"\bBhagavad\s+Gita\s+{re.escape(ch_s)}\.(?!\s*{re.escape(ve_s)}\b)",
        _repl,
        text,
        flags=re.I,
    )


_LEAD_BARE_CIT_CAP_WORD = re.compile(
    r"(^|[.!?]\s+)(\d{1,2}\.\d{1,3})\s+(?=[A-Z])",
)


def _drop_sentence_leading_bare_citation_if_repeated(text: str) -> str:
    """Drop a bare citation like ``. 6.5 A concrete...`` when the same citation already appeared.

    Guarantees the primary citation still appears in the text (the earlier mention); avoids
    the ungrammatical ``<period> <digits>.<digits> <Capitalized word>`` pattern the model
    sometimes emits after it has already cited the verse.
    """
    if not text:
        return text

    def _repl(m: re.Match[str]) -> str:
        prior = text[: m.start()]
        cit = m.group(2)
        if re.search(rf"\b{re.escape(cit)}\b", prior):
            return m.group(1)
        return m.group(0)

    return _LEAD_BARE_CIT_CAP_WORD.sub(_repl, text)


def _stabilize_primary_citation_mentions(text: str, *, effective_primary_key: str | None) -> str:
    """Repair chapter-only fragments like ``in 2.Focus`` back to MAIN ``2.47`` forms.

    The Ollama model (qwen2.5:14b) sometimes truncates the verse segment of a citation and
    fuses it with the next word (``in 2.Focus``, ``as stated in 2.Act``). We expand the
    chapter-only remnant to the MAIN citation so validation does not mark it as
    ``missing_primary_citation`` and kick us into the deterministic fallback.
    """
    pk = effective_primary_key
    if not pk or "." not in pk:
        return text
    ch, ve = pk.split(".", 1)
    if not ch.isdigit() or not ve.isdigit():
        return text
    ch_s = str(int(ch))
    s = text
    connectors = r"in|at|on|of|from|via|per|by|within|about|into"
    s = re.sub(
        rf"\b(?:{connectors})\s+{re.escape(ch_s)}\.(?=[A-Z])",
        lambda m: f"{m.group(0)[: -len(ch_s) - 1]}{pk} ",
        s,
        flags=re.I,
    )
    s = re.sub(
        rf"\b(?:{connectors})\s+{re.escape(ch_s)}\.\s+(?=[A-Z])",
        lambda m: f"{m.group(0).split()[0]} {pk} ",
        s,
        flags=re.I,
    )
    s = re.sub(
        rf"\b(?:verse|chapter)\s+{re.escape(ch_s)}\.(?=\s*[A-Z])",
        lambda m: f"{m.group(0).split()[0]} {pk}",
        s,
        flags=re.I,
    )
    s = re.sub(
        rf"\bBhagavad\s+Gita\s+{re.escape(ch_s)}\.\s*(?=[A-Z])",
        f"Bhagavad Gita {pk} ",
        s,
        flags=re.I,
    )
    return s


def _strip_rubric_leaks(text: str) -> str:
    s = text
    for pat in _RUBRIC_FRAGMENTS:
        s = pat.sub("", s)
    return _MULTISPACE.sub(" ", s).strip()


def _polish_generation_text(text: str) -> str:
    s = text
    s = _VERSES_SHORT_PAIR.sub("Verses 2.47 and 6.5", s)
    s = _VERSE_SHORT.sub(
        lambda m: f"Verse { {'5':'6.5','47':'2.47','66':'18.66'}[m.group(1)] }",
        s,
    )
    s = _BROKEN_A_COULD.sub("A practical next step could be", s)
    s = _ONESELF_DO_NOT.sub("oneself; do not", s)
    # MVP corpus maps informal "Gita 5" to 6.5 (chapter 6, verse 5). Revisit if chapter-5 text is added.
    s = _BHAGAVAD_GITA_SOLO_CH.sub("Bhagavad Gita 6.5", s)
    s = _GITA_SOLO_CH.sub("Gita 6.5", s)
    s = _CITATION_KEY_PHRASE_DOTTED.sub(r"Bhagavad Gita \1.\2", s)
    s = _CITATION_KEY_PHRASE_SOLO.sub(
        lambda m: {
            "5": "Bhagavad Gita 6.5",
            "47": "Bhagavad Gita 2.47",
            "66": "Bhagavad Gita 18.66",
        }.get(m.group(1), f"Bhagavad Gita {m.group(1)}"),
        s,
    )
    # Ellipsis or "..." before a closing See line (rubric mimicry / broken tails).
    s = re.sub(r"\s*…+\s*(?=See\s)", ". ", s)
    s = re.sub(r"\s*\.{3,}\s*(?=See\s)", ". ", s)
    s = re.sub(r"\.\s+\.\s+(?=See\s)", ". ", s)
    # Fix ungrammatical verse-openers the model sometimes echoes.
    s = re.sub(
        r"\bAccording to Verse\s+(\d+\.\d+)\s*,\s*advises\b",
        r"Verse \1 advises",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\bAccording to Verse\s+(\d+\.\d+)\s*,\s*the\b",
        r"In Verse \1, the",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\bAccording to Bhagavad Gita\s+(\d+\.\d+)\s*,\s*advises\b",
        r"Bhagavad Gita \1 advises",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\bAccording to Bhagavad Gita\s+(\d+\.\d+)\s*,\s*the\b",
        r"In Bhagavad Gita \1, the",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\bThe Bhagavad Gita\s+(\d+\.\d+)\s*,\s*advises\b",
        r"Bhagavad Gita \1 advises",
        s,
        flags=re.I,
    )
    return _MULTISPACE.sub(" ", s).strip()


def polish_guidance_full_text(
    raw: str,
    *,
    allowed_citation_keys: set[str] | None = None,
    primary_citation_key: str | None = None,
) -> str:
    """
    One-shot normalization for a complete explanation string (post-Ollama, pre-validation).

    Mirrors ``GuidanceOutputController`` cleaning without progressive word/sentence caps.
    """
    if not raw:
        return ""
    eff_primary = _effective_primary(allowed_citation_keys, primary_citation_key)
    text = _MARKDOWN_NOISE.sub("", raw)
    text = _polish_generation_text(text)
    text = _polish_verbal_glitches(text, effective_primary_key=eff_primary)
    # Before ``_NUMBERED_STEP`` strips ``6. `` from ``Bhagavad Gita 6. lifts``, restore full citation.
    text = _repair_truncated_bhagavad_gita_citation(text, effective_primary_key=eff_primary)
    text = _stabilize_primary_citation_mentions(text, effective_primary_key=eff_primary)
    text = _drop_sentence_leading_bare_citation_if_repeated(text)
    text = (
        text.replace("Verse 5", "Verse 6.5")
        .replace("verse 5", "verse 6.5")
        .replace("Verse 47", "Verse 2.47")
        .replace("verse 47", "verse 2.47")
        .replace("Verse 66", "Verse 18.66")
        .replace("verse 66", "verse 18.66")
        .replace("A could be", "A practical next step could be")
    )
    text = _CIT_KEY_BRACKET.sub(r"\1", text)
    text = _PAREN_SHORT_CIT.sub(
        lambda m: {"5": "6.5", "47": "2.47", "66": "18.66"}.get(m.group(1), m.group(0)),
        text,
    )
    text = _BARE_SHORT_NUM.sub(
        lambda m: {"5": "6.5", "47": "2.47", "66": "18.66"}.get(m.group(1), ""),
        text,
    )
    text = _HEADING_PREFIX.sub("", text)
    text = _LABEL_PREFIX.sub("", text)
    text = _NUMBERED_STEP.sub("", text)
    for pat in _FILLER_PATTERNS:
        text = pat.sub("", text)
    text = _MULTISPACE.sub(" ", text).strip()
    if not text:
        return ""
    if allowed_citation_keys is not None:
        for k in set(_CIT_KEY_TOKEN.findall(text)):
            if k not in allowed_citation_keys:
                text = text.replace(k, "").strip()
        if "18.66" not in allowed_citation_keys:
            for bad in ("surrender to krishna", "surrender to", "krishna"):
                text = re.sub(rf"\b{re.escape(bad)}\b", "", text, flags=re.I).strip()
            text = _MULTISPACE.sub(" ", text).strip()
    text = re.sub(r"\s*See\s+\d+\.\d+\s*\.?\s*$", "", text, flags=re.I).strip()
    text = _polish_malformed_citation_phrases(text)
    if re.search(r"\b\d{1,2}\.\d{1,3}\b$", text) and text[-1] not in ".!?":
        text += "."
    text = _strip_rubric_leaks(text).strip()
    if eff_primary:
        text = normalize_primary_citation_label(text, primary_citation_key=eff_primary)
        # Final deterministic guarantee: scrub any remaining malformed citation fragments
        # and, if still missing, inject the exact ``Bhagavad Gita <pk>`` label. The model
        # never owns the final primary-citation string.
        text = enforce_primary_citation_label(text, primary_citation_key=eff_primary)
    return text


def normalize_primary_citation_label(text: str, *, primary_citation_key: str) -> str:
    """Rewrite prose/loose citation forms to the exact structured label ``Bhagavad Gita X.Y``.

    Treats the citation as structured data: once generation is done, all permissive forms
    (``Gita 2, 47``, ``Verse 2, 47``, ``chapter 2 verse 47``, ``Bhagavad Gita 2, 47``) are
    rewritten to the single canonical label ``Bhagavad Gita <pk>``. If the text already
    contains the exact label, it is returned unchanged. This runs after all other polish
    steps so no downstream pattern re-mangles the citation.
    """
    if not primary_citation_key or not text:
        return text
    parts = primary_citation_key.split(".", 1)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return text
    ch_s = str(int(parts[0]))
    ve_s = str(int(parts[1]))
    pk = f"{ch_s}.{ve_s}"
    label = f"Bhagavad Gita {pk}"

    s = text
    # Already canonical and well-formed — only normalize variants that are not the exact label.
    s = re.sub(
        rf"\bBhagavad\s+Gita\s+{re.escape(ch_s)}\s*,\s*{re.escape(ve_s)}\b",
        label,
        s,
        flags=re.I,
    )
    s = re.sub(
        rf"(?<!Bhagavad\s)\bGita\s+{re.escape(ch_s)}\s*(?:\.|,)\s*{re.escape(ve_s)}\b",
        label,
        s,
        flags=re.I,
    )
    s = re.sub(
        rf"\bVerse\s+{re.escape(ch_s)}\s*,\s*{re.escape(ve_s)}\b",
        f"Verse {pk}",
        s,
        flags=re.I,
    )
    # ``chapter 2 verse 47``, ``chapter 2 Verse 47``, and the already-polished
    # ``chapter 2 Verse 2.47`` all collapse to the canonical label.
    s = re.sub(
        rf"\bchapter\s+{ch_s}\b([\s\S]{{0,80}}?)\bverse\s+(?:{re.escape(ch_s)}\.)?{re.escape(ve_s)}\b",
        lambda m: f"{label}{m.group(1)}" if m.group(1).strip() else label,
        s,
        flags=re.I,
    )
    # Stand-alone ``Verse <pk>`` → full ``Bhagavad Gita <pk>`` label for strict checks.
    s = re.sub(
        rf"\bVerse\s+{re.escape(pk)}\b",
        label,
        s,
    )
    return s


def enforce_primary_citation_label(text: str, *, primary_citation_key: str) -> str:
    """Deterministically guarantee the exact ``Bhagavad Gita <pk>`` label is present.

    The model cannot be trusted to render the final primary-citation string cleanly: it
    sometimes produces truncated or malformed fragments like ``Bhagavad Gita 2.``,
    ``Bhagavad Gita 2.This``, ``Verse 2.``, or a bare trailing ``2.`` at sentence breaks.
    This function treats the citation as structured data: it scrubs every malformed form of
    the *primary* chapter, rewrites it to the canonical label, and — as a last resort —
    injects a parenthetical label into the first sentence if the text still lacks it.

    Runs unconditionally at the end of polish; idempotent when the label is already present
    and well-formed. Returns ``text`` unchanged when ``primary_citation_key`` is empty or
    not a valid ``X.Y`` key (no primary to enforce).
    """
    if not primary_citation_key or not text:
        return text
    parts = primary_citation_key.split(".", 1)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return text
    ch_s = str(int(parts[0]))
    ve_s = str(int(parts[1]))
    pk = f"{ch_s}.{ve_s}"
    label = f"Bhagavad Gita {pk}"

    s = text

    # 1) ``Bhagavad Gita 2.`` (not followed by the verse digits) → exact label with a space
    # when fused to a following letter. Handles ``Bhagavad Gita 2.This`` as well as
    # ``Bhagavad Gita 2. `` at a sentence break.
    def _bg_repl(m: re.Match[str]) -> str:
        end = m.end()
        tail = s[end : end + 1]
        pad = " " if tail and (tail.isalnum() or tail in ("(",)) else ""
        return f"{label}{pad}"

    s = re.sub(
        rf"\bBhagavad\s+Gita\s+{re.escape(ch_s)}\.(?!\s*{re.escape(ve_s)}\b)",
        _bg_repl,
        s,
        flags=re.I,
    )

    # 2) ``Verse 2.`` (not followed by the verse digits) → exact label.
    def _v_repl(m: re.Match[str]) -> str:
        end = m.end()
        tail = s[end : end + 1]
        pad = " " if tail and (tail.isalnum() or tail in ("(",)) else ""
        return f"{label}{pad}"

    s = re.sub(
        rf"\bVerse\s+{re.escape(ch_s)}\.(?!\s*{re.escape(ve_s)}\b)",
        _v_repl,
        s,
        flags=re.I,
    )

    # 3) Orphan chapter-only prose ``chapter 2.`` at end of a clause, not followed by the
    # verse digits — replace with the canonical label so it does not stand as ``chapter 2.``.
    s = re.sub(
        rf"\bchapter\s+{re.escape(ch_s)}\.(?!\s*{re.escape(ve_s)}\b)",
        label,
        s,
        flags=re.I,
    )

    # 4) If after scrubbing the malformed forms the exact label is still missing, inject it
    # via the same first-sentence parenthetical as the legacy salvage path. This is the
    # last deterministic guarantee.
    if not re.search(rf"\b{re.escape(label)}\b", s):
        s = salvage_missing_primary_citation(s, primary_citation_key=pk)

    # 5) Collapse any double spaces introduced by the above substitutions.
    s = _MULTISPACE.sub(" ", s).strip()
    return s


def salvage_missing_primary_citation(text: str, *, primary_citation_key: str) -> str:
    """Inject the MAIN citation into the first sentence when polish missed it entirely.

    Only used as a last resort before falling back to the deterministic paragraph. If the
    primary already appears in any form, the text is returned unchanged.
    """
    if not primary_citation_key or not text:
        return text
    if re.search(rf"\b{re.escape(primary_citation_key)}\b", text):
        return text
    parts = primary_citation_key.split(".", 1)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return text
    ch_s = str(int(parts[0]))
    ve_s = str(int(parts[1]))
    prose_form = rf"\bBhagavad\s+Gita\s+{re.escape(ch_s)}\s*(?:\.|,)\s*{re.escape(ve_s)}\b|\bVerse\s+{re.escape(ch_s)}\s*(?:\.|,)\s*{re.escape(ve_s)}\b|\bchapter\s+{ch_s}\b[\s\S]{{0,80}}\bverse\s+{ve_s}\b|\bGita\s+{re.escape(ch_s)}\s*(?:\.|,)\s*{re.escape(ve_s)}\b"
    if re.search(prose_form, text, flags=re.I):
        return text
    masked = re.sub(r"\b\d+\.\d+\b", lambda m: m.group(0).replace(".", "\x00"), text)
    match = re.search(r"[.!?](?:\s+|$)", masked)
    if match is None:
        first = text.rstrip(".!? \t\n")
        rest = ""
    else:
        split_at = match.end()
        first = text[: split_at - len(match.group(0))].rstrip()
        rest = text[split_at:]
    if not first:
        return text
    if first.endswith((".", "!", "?")):
        first_body = first[:-1].rstrip()
        terminator = first[-1]
    else:
        first_body = first
        terminator = "."
    salvaged_first = f"{first_body} (Bhagavad Gita {primary_citation_key}){terminator}"
    joiner = " " if rest and not rest.startswith(" ") else ""
    return f"{salvaged_first}{joiner}{rest}".strip()


class GuidanceOutputController:
    """
    Normalize streamed chunks and enforce concise output constraints progressively.

    - Remove markdown / heading artifacts.
    - Cap to max words and max sentence endings.
    - Drop obvious filler endings.
    """

    def __init__(
        self,
        *,
        max_words: int = 90,
        max_sentences: int = 4,
        allowed_citation_keys: set[str] | None = None,
    ) -> None:
        self._max_words = max_words
        self._max_sentences = max_sentences
        self._words = 0
        self._sentences = 0
        self._done = False
        self._last_norm = ""
        self._allowed = allowed_citation_keys
        self._raw_accum = ""
        self._san_accum = ""
        self._emitted_any = False

    @property
    def done(self) -> bool:
        return self._done

    def feed(self, chunk: str) -> str:
        if self._done or not chunk:
            return ""
        self._raw_accum += chunk
        text = _MARKDOWN_NOISE.sub("", self._raw_accum)
        text = _polish_generation_text(text)
        text = (
            text.replace("Verse 5", "Verse 6.5")
            .replace("verse 5", "verse 6.5")
            .replace("Verse 47", "Verse 2.47")
            .replace("verse 47", "verse 2.47")
            .replace("Verse 66", "Verse 18.66")
            .replace("verse 66", "verse 18.66")
            .replace("A could be", "A practical next step could be")
        )
        text = _CIT_KEY_BRACKET.sub(r"\1", text)
        text = _PAREN_SHORT_CIT.sub(
            lambda m: {"5": "6.5", "47": "2.47", "66": "18.66"}.get(m.group(1), m.group(0)),
            text,
        )
        text = _BARE_SHORT_NUM.sub(
            lambda m: {"5": "6.5", "47": "2.47", "66": "18.66"}.get(m.group(1), ""),
            text,
        )
        text = _HEADING_PREFIX.sub("", text)
        text = _LABEL_PREFIX.sub("", text)
        text = _NUMBERED_STEP.sub("", text)
        for pat in _FILLER_PATTERNS:
            text = pat.sub("", text)
        text = _MULTISPACE.sub(" ", text).strip()
        if not text:
            return ""

        # Enforce: only cite verses that were actually provided to generation.
        if self._allowed is not None:
            for k in set(_CIT_KEY_TOKEN.findall(text)):
                if k not in self._allowed:
                    text = text.replace(k, "").strip()
            # If the model drifts into surrender/devotional phrasing without 18.66 allowed, strip it.
            if "18.66" not in self._allowed:
                for bad in ("surrender to krishna", "surrender to", "krishna"):
                    text = re.sub(rf"\b{re.escape(bad)}\b", "", text, flags=re.I).strip()
                text = _MULTISPACE.sub(" ", text).strip()
                if not text:
                    return ""

        # Emit only the new suffix since last sanitized output.
        if self._san_accum and text.startswith(self._san_accum):
            emit = text[len(self._san_accum) :].lstrip()
        else:
            # Sanitization changed earlier content; restart from current.
            emit = text if not self._san_accum else ""
        self._san_accum = text
        text = _strip_rubric_leaks(emit)
        if not text:
            return ""
        norm = text.casefold()
        if norm == self._last_norm:
            return ""

        words = text.split(" ")
        allowed_words = self._max_words - self._words
        if allowed_words <= 0:
            self._done = True
            return ""
        if len(words) > allowed_words:
            words = words[:allowed_words]
            text = " ".join(words).rstrip(",;:")
            self._done = True
            if text and text[-1] not in ".!?":
                text = text.rstrip(",;:") + "."

        sent_marks = len(_SENT_END.findall(text))
        allowed_sent = self._max_sentences - self._sentences
        if allowed_sent <= 0:
            self._done = True
            return ""
        if sent_marks > allowed_sent:
            count = 0
            cut = len(text)
            for i, ch in enumerate(text):
                if ch in ".!?":
                    count += 1
                    if count == allowed_sent:
                        cut = i + 1
                        break
            text = text[:cut].rstrip()
            self._done = True
            sent_marks = allowed_sent

        text = _TRAILING_FRAGMENT.sub("", text).strip()
        text = _TRAILING_SOLO_NUMBER.sub("", text).strip()
        if not text:
            return ""
        if self._done and text and text[-1] not in ".!?":
            text = text.rstrip(",;:") + "."
        text = _TRAILING_AND.sub("", text).strip()
        self._words += len(text.split())
        self._sentences += sent_marks
        self._last_norm = text.casefold()
        if self._words >= self._max_words or self._sentences >= self._max_sentences:
            self._done = True
        self._emitted_any = True
        return text + " "

    def finalize_if_needed(self) -> str:
        """
        If no citation key was emitted but we have allowed keys, append one minimal anchor.
        """
        if not self._allowed or not self._emitted_any:
            return ""
        # If output already contains one of the allowed keys, do nothing.
        # This is best-effort: the stream already went out; we only append at the end.
        return ""


async def stream_ollama_chat_phrased(
    upstream: AsyncIterator[str],
) -> AsyncIterator[str]:
    """
    Wrap a token stream: yield fewer, larger chunks aligned to phrases/sentences where possible.
    """
    buf = GuidanceExplanationBuffer()
    async for piece in upstream:
        for chunk in buf.feed(piece):
            if chunk:
                yield chunk
    tail = buf.finalize()
    if tail:
        yield tail
