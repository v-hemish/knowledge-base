"""Post-generation validation for guidance explanations."""

from __future__ import annotations

from app.llm.guidance_validation import (
    build_regeneration_instruction,
    deterministic_fallback_explanation,
    mentions_primary_citation,
    trim_explanation_to_limits,
    validate_guidance_explanation,
)
from app.llm.query_intent import QueryProfile


def _p(**kwargs: bool) -> QueryProfile:
    return QueryProfile(
        distress=kwargs.get("distress", False),
        burnout=kwargs.get("burnout", False),
        discipline=kwargs.get("discipline", False),
        moral_conflict=kwargs.get("moral_conflict", False),
        surrender_explicit=kwargs.get("surrender_explicit", False),
        action_without_fruit=kwargs.get("action_without_fruit", False),
        faith_grace_language=kwargs.get("faith_grace_language", False),
    )


def test_mentions_primary_accepts_bhagavad_gita_comma_form() -> None:
    t = "The counsel in Bhagavad Gita 2, 47 is to act without clinging to every outcome."
    assert mentions_primary_citation(t, primary_citation_key="2.47")


def test_mentions_primary_accepts_chapter_and_verse_prose() -> None:
    t = "In chapter 2 verse 47, duty stays steady without owning every result."
    assert mentions_primary_citation(t, primary_citation_key="2.47")


def test_mentions_primary_accepts_gita_short_form() -> None:
    t = "Gita 2, 47 keeps effort distinct from owning every outcome."
    assert mentions_primary_citation(t, primary_citation_key="2.47")


def test_validate_requires_exact_primary_label_for_duty_answer() -> None:
    """Prose-only citation ``chapter 2 verse 47`` is no longer accepted at final-validate.

    Structured-data contract: final output must contain the exact ``Bhagavad Gita 2.47`` label.
    The permissive form is still recognized by ``mentions_primary_citation`` for regeneration
    hints, but now triggers ``missing_primary_citation_label`` to force the label in.
    """
    prose_only = (
        "In chapter 2 verse 47, right action stays steady without clinging to every outcome you cannot control. "
        "Name one bounded task before you reopen the dashboard."
    )
    vr_prose = validate_guidance_explanation(
        prose_only,
        primary_citation_key="2.47",
        allowed={"2.47", "6.5"},
        profile=_p(),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert not vr_prose.ok
    assert "missing_primary_citation" not in vr_prose.reasons
    assert "missing_primary_citation_label" in vr_prose.reasons

    structured = (
        "Bhagavad Gita 2.47 holds right action steady without clinging to every outcome you cannot control. "
        "Name one bounded task before you reopen the dashboard."
    )
    vr_struct = validate_guidance_explanation(
        structured,
        primary_citation_key="2.47",
        allowed={"2.47", "6.5"},
        profile=_p(),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert vr_struct.ok, vr_struct.reasons


def test_validate_accepts_thematic_opening_with_citation() -> None:
    text = (
        "The emphasis here is on steadying action while leaving fruits aside; Bhagavad Gita 2.47 states that plainly for work obsession. "
        "One small move is picking a single task you will complete before you check metrics."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47", "6.5"},
        profile=_p(),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert vr.ok


def test_validate_rejects_verse_teaches_opening() -> None:
    text = (
        "Verse 2.47 teaches that you have a right to action alone, not to fruits. "
        "Try one bounded task today. Pause before checking metrics."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert not vr.ok
    assert "stock_verse_teaches_opening" in vr.reasons


def test_validate_rejects_closing_see_line() -> None:
    text = (
        "Bhagavad Gita 2.47 separates effort from owning every result. "
        "That can ease obsession when you name what you control. "
        "Try one bounded task today. See 2.47."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47", "6.5"},
        profile=_p(burnout=True),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert not vr.ok
    assert "closing_see_citation_line" in vr.reasons


def test_validate_accepts_this_passage_style_opening() -> None:
    """‘This passage…’ is allowed; validation targets therapist templates only."""
    text = (
        "This passage keeps duty steady without clinging to every metric swing; Bhagavad Gita 2.47 names that plainly. "
        "Try one bounded task before you reopen the dashboard."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47", "6.5"},
        profile=_p(burnout=True),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert vr.ok


def test_validate_rejects_banned_opening() -> None:
    text = (
        "It sounds like work pressure is heavy. Bhagavad Gita 2.47 names action without clinging to fruits. "
        "Try one bounded task today."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert not vr.ok
    assert "banned_empathy_opening" in vr.reasons


def test_validate_rejects_stock_reflection_question() -> None:
    text = (
        "These verses shift attention from owning every scoreboard swing. "
        "Bhagavad Gita 2.47 keeps right with action and loosens fruit-fixation. "
        "How will you start applying this when the urge to check returns?"
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert not vr.ok
    assert "stock_reflection_question" in vr.reasons


def test_validate_rejects_grammar_fragment() -> None:
    text = (
        "Verse 6.5 speaks to lifting oneself through self-discipline avoid degrading yourself. "
        "Name one small window for practice."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="6.5",
        allowed={"6.5", "2.47"},
        profile=_p(discipline=True),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert not vr.ok
    assert "grammar_artifact" in vr.reasons


def test_validate_distress_passes_with_warmth_not_hotline() -> None:
    text = (
        "Here the focus is on befriending the mind rather than turning inward as an enemy when thoughts spiral; Bhagavad Gita 6.5 names that in a gentle register. "
        "A quiet pace matters more than forcing a mood shift when days feel empty. "
        "Try five minutes with the passage alone, without grading yourself."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="6.5",
        allowed={"6.5", "2.47"},
        profile=_p(distress=True),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert vr.ok


def test_build_regeneration_instruction_mentions_variety() -> None:
    s = build_regeneration_instruction(("too_long",), primary_citation_key="2.47")
    assert "2.47" in s
    assert "teaches" in s.lower()


def test_deterministic_fallback_has_no_see_line() -> None:
    t = deterministic_fallback_explanation(primary_citation_key="2.47")
    assert "See 2.47" not in t
    assert "2.47" in t
    assert "clearest guidance" in t.lower() or "bhagavad gita" in t.lower()


def test_validate_rejects_abrupt_punctuation_at_end() -> None:
    text = ("Bhagavad Gita 2.47 asks for faithful action while releasing fixation on metrics. " * 2).strip() + ":"
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert not vr.ok
    assert "abrupt_punctuation_ending" in vr.reasons


def test_validate_rejects_unbalanced_quotes() -> None:
    text = (
        "Bhagavad Gita 2.47 says to work without clinging to fruits. "
        "That can ease obsession when you name what you control. \"Still broken."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert not vr.ok
    assert "unfinished_or_unbalanced_quotes" in vr.reasons


def test_validate_distress_allows_single_discipline_stock_in_concise_grief_answer() -> None:
    """Grief-shaped answers should not fail only for one ‘steady effort’ without kindness lexicon."""
    text = (
        "Bhagavad Gita 6.5 names steady effort without turning inward as an enemy when grief hollows the day. "
        "Read the lines once without fixing anything or grading yourself."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="6.5",
        allowed={"6.5", "2.47"},
        profile=_p(distress=True),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert vr.ok


def test_validate_distress_allows_two_discipline_stock_phrases() -> None:
    text = (
        "Bhagavad Gita 6.5 names steady effort without turning inward as an enemy when grief hollows the day. "
        "Lift yourself gently in small steps rather than as a performance. "
        "Give the lines a few quiet minutes without grading yourself."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="6.5",
        allowed={"6.5", "2.47"},
        profile=_p(distress=True),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert vr.ok


def test_validate_distress_rejects_triple_discipline_stock() -> None:
    text = (
        "Verse 6.5 points toward self-mastery through steady effort rather than collapse. "
        "Self-mastery here means self-discipline rather than harsh blame every hour. "
        "Just discipline alone cannot heal grief, yet steady effort still matters in small doses."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="6.5",
        allowed={"6.5", "2.47"},
        profile=_p(distress=True),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert not vr.ok
    assert "distress_discipline_stock_phrases" in vr.reasons


def test_validate_rejects_rubric_stage_leak() -> None:
    text = (
        "Verse 6.5 steadies effort without harsh self-blame. "
        "Ending with a small concrete next step: pause before the next spiral."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="6.5",
        allowed={"6.5"},
        profile=_p(),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert not vr.ok
    assert "template_rubric_leak" in vr.reasons


def test_validate_rejects_malformed_chapter_only_bhagavad_gita_reference() -> None:
    text = (
        "Your duty is to act without seeking control over the outcomes, as emphasized by "
        "Bhagavad Gita 2. Focus on effort rather than results."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert not vr.ok
    assert "malformed_verse_reference" in vr.reasons


def test_validate_rejects_malformed_chapter_only_verse_reference() -> None:
    text = (
        "Verse 6. speaks to lifting oneself with care rather than harsh blame. "
        "Try one small step today."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="6.5",
        allowed={"6.5"},
        profile=_p(),
        min_words=18,
        max_words=72,
        max_sentences=3,
    )
    assert not vr.ok
    assert "malformed_verse_reference" in vr.reasons


def test_validate_rejects_prose_only_primary_without_exact_label() -> None:
    """Prose-only citations (``chapter 2 verse 47``) must no longer pass final validation."""
    text = (
        "In chapter 2 verse 47, Krishna reminds you to act without clinging to fruit. "
        "Finish the task in front of you and let the outcome unfold without claiming it."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert not vr.ok
    assert "missing_primary_citation_label" in vr.reasons
    assert "missing_primary_citation" not in vr.reasons


def test_validate_accepts_exact_primary_citation_label() -> None:
    text = (
        "Bhagavad Gita 2.47 sets the task plainly: act without claiming the result in advance. "
        "Finish the work that is yours and leave the yield to unfold."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert vr.ok, vr.reasons


def test_deterministic_fallback_is_verse_specific_for_non_distress() -> None:
    from app.llm.guidance_validation import deterministic_fallback_explanation

    for pk in ("2.47", "6.5", "18.66"):
        txt = deterministic_fallback_explanation(primary_citation_key=pk, distress=False)
        assert f"Bhagavad Gita {pk}" in txt
        assert "read that passage on its own terms" not in txt, (
            "non-sensitive fallback must be verse-specific, not the soft template"
        )


def test_deterministic_fallback_is_soft_for_distress() -> None:
    from app.llm.guidance_validation import deterministic_fallback_explanation

    txt = deterministic_fallback_explanation(
        primary_citation_key="2.47",
        distress=True,
        surrender_explicit=False,
    )
    assert "Bhagavad Gita 2.47" in txt
    assert "trusted person" in txt


def test_deterministic_fallback_surrender_explicit_prefers_verse_specific() -> None:
    from app.llm.guidance_validation import deterministic_fallback_explanation

    txt = deterministic_fallback_explanation(
        primary_citation_key="18.66",
        distress=True,
        surrender_explicit=True,
    )
    assert "Bhagavad Gita 18.66" in txt
    assert "refuge" in txt


def test_validate_rejects_orphan_leading_bare_citation() -> None:
    text = (
        "Bhagavad Gita 6.5 stresses steady effort without harsh blame. "
        "6.5 A concrete next step is setting a small manageable goal."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="6.5",
        allowed={"6.5"},
        profile=_p(),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert not vr.ok
    assert "orphan_leading_bare_citation" in vr.reasons


def test_validate_rejects_malformed_citation_phrase() -> None:
    text = (
        "Bhagavad Gita 6.5 points toward in 6.5 steady effort without harsh blame. "
        "Try one small step today."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="6.5",
        allowed={"6.5"},
        profile=_p(),
        min_words=20,
        max_words=72,
        max_sentences=3,
    )
    assert not vr.ok
    assert "malformed_citation_phrase" in vr.reasons


def test_validate_rejects_too_many_sentences() -> None:
    text = (
        "Bhagavad Gita 2.47 names action without clinging to fruits. "
        "That loosens scoreboard fixation. "
        "Try one bounded task. "
        "Pause before checking metrics. "
        "What boundary helps tomorrow?"
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert not vr.ok
    assert "too_many_sentences" in vr.reasons


def test_validate_rejects_meta_citation_key_in_body() -> None:
    text = (
        "The passage called citation key 2.47 names action without clinging to fruits. "
        "That can ease obsession when you name what you control. "
        "Try one bounded task today without checking the score."
    )
    vr = validate_guidance_explanation(
        text,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert not vr.ok
    assert "meta_citation_key_leak" in vr.reasons


def test_trim_explanation_drops_trailing_sentences() -> None:
    raw = (
        "Bhagavad Gita 2.47 names action without clinging to fruits of labor you cannot finally own or control. "
        "That loosens scoreboard fixation when honest effort is enough for the day. "
        "Try one bounded task you can finish without checking dashboards until it is done. "
        "Pause before checking metrics when the urge to compare arrives. "
        "What boundary helps tomorrow?"
    )
    out = trim_explanation_to_limits(raw, max_words=85, max_sentences=4)
    vr = validate_guidance_explanation(
        out,
        primary_citation_key="2.47",
        allowed={"2.47"},
        profile=_p(),
        min_words=22,
        max_words=85,
        max_sentences=4,
    )
    assert vr.ok
