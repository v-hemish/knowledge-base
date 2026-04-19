"""Guidance explanation stream buffering (phrase / sentence chunks)."""

from __future__ import annotations

import asyncio
import re

from app.llm.stream_buffer import (
    GuidanceExplanationBuffer,
    GuidanceOutputController,
    enforce_primary_citation_label,
    normalize_primary_citation_label,
    polish_guidance_full_text,
    salvage_missing_primary_citation,
    stream_ollama_chat_phrased,
)


def test_enforce_primary_citation_label_repairs_bhagavad_gita_2_dot_this() -> None:
    raw = (
        "Your duty is to act without seeking control over the outcomes, as emphasized by "
        "Bhagavad Gita 2.This means focusing on your actions rather than their results."
    )
    out = enforce_primary_citation_label(raw, primary_citation_key="2.47")
    assert "Bhagavad Gita 2.47 This" in out
    assert "Bhagavad Gita 2.This" not in out
    assert "Bhagavad Gita 2." not in out.replace("Bhagavad Gita 2.47", "")


def test_enforce_primary_citation_label_repairs_verse_chapter_only() -> None:
    raw = "The teaching in Verse 6.is to lift yourself by steady effort."
    out = enforce_primary_citation_label(raw, primary_citation_key="6.5")
    assert "Bhagavad Gita 6.5 is" in out
    assert "Verse 6." not in out.replace("Bhagavad Gita 6.5", "")


def test_enforce_primary_citation_label_injects_when_label_absent() -> None:
    """If no form of the primary citation is present, inject parenthetical into first sentence."""
    raw = "Act without obsessing over outcomes and keep the work itself as the focus."
    out = enforce_primary_citation_label(raw, primary_citation_key="2.47")
    assert "Bhagavad Gita 2.47" in out


def test_enforce_primary_citation_label_is_idempotent_when_label_present() -> None:
    raw = "Bhagavad Gita 2.47 sets the task plainly: do the work and let outcomes unfold."
    out = enforce_primary_citation_label(raw, primary_citation_key="2.47")
    assert out == raw


def test_polish_end_to_end_rescues_duty_outcomes_rejected_draft() -> None:
    """Exact rejected draft from a live duty_outcomes capture should polish to clean output."""
    raw = (
        "Your duty is to act without seeking control over the outcomes, as emphasized by "
        "Bhagavad Gita 2.This means focusing on your actions rather than their results."
    )
    polished = polish_guidance_full_text(
        raw,
        allowed_citation_keys={"2.47", "18.66"},
        primary_citation_key="2.47",
    )
    assert "Bhagavad Gita 2.47" in polished
    assert "Bhagavad Gita 2.This" not in polished
    assert "Bhagavad Gita 2." not in polished.replace("Bhagavad Gita 2.47", "")


def test_normalize_primary_citation_label_rewrites_gita_comma_form() -> None:
    out = normalize_primary_citation_label(
        "Gita 2, 47 reminds you to act without clinging to the outcome.",
        primary_citation_key="2.47",
    )
    assert "Bhagavad Gita 2.47" in out
    assert "Gita 2, 47" not in out


def test_normalize_primary_citation_label_rewrites_chapter_verse_prose() -> None:
    out = normalize_primary_citation_label(
        "In chapter 2 verse 47, the way is set plainly.",
        primary_citation_key="2.47",
    )
    assert "Bhagavad Gita 2.47" in out
    assert "chapter 2" not in out.lower()


def test_normalize_primary_citation_label_leaves_exact_label_untouched() -> None:
    text = "Bhagavad Gita 6.5 steadies the self without harsh blame."
    assert normalize_primary_citation_label(text, primary_citation_key="6.5") == text


def test_polish_enforces_exact_primary_label_for_prose_form() -> None:
    raw = (
        "In chapter 2 verse 47, the teaching is plain: act without clinging to the yield. "
        "Finish the task in front of you and let the result unfold without claiming it."
    )
    polished = polish_guidance_full_text(
        raw,
        allowed_citation_keys={"2.47"},
        primary_citation_key="2.47",
    )
    assert "Bhagavad Gita 2.47" in polished


def test_buffer_emits_on_sentence_boundary() -> None:
    buf = GuidanceExplanationBuffer()
    out: list[str] = []
    for piece in ["One two. ", "Three four."]:
        out.extend(buf.feed(piece))
    out.append(buf.finalize())
    assert out == ["One two. ", "Three four."]
    assert "".join(out) == "One two. Three four."


def test_buffer_first_flush_on_space_when_no_punct() -> None:
    buf = GuidanceExplanationBuffer(first_flush_min_total=10, first_flush_space_min_index=4)
    chunks = []
    chunks.extend(buf.feed("abcd efgh ijkl"))
    # After min length, first space from index 4 → space after "abcd" at position 4
    assert len(chunks) >= 1
    assert chunks[0].startswith("abcd ")
    rest = buf.finalize()
    assert "efgh" in rest or "ijkl" in rest


def test_buffer_hard_max_without_spaces() -> None:
    buf = GuidanceExplanationBuffer(first_flush_min_total=10_000, soft_max=10_000, hard_max=25)
    chunks = buf.feed("z" * 60)
    assert sum(len(c) for c in chunks) + len(buf.finalize()) == 60
    assert all(len(c) <= 25 for c in chunks)


async def test_phrased_stream_coalesces_tokens() -> None:
    async def upstream() -> asyncio.AsyncIterator[str]:
        yield "Hello"
        yield " world"
        yield ". "
        yield "Next"

    parts: list[str] = []
    async for c in stream_ollama_chat_phrased(upstream()):
        parts.append(c)
    assert "Hello world. " in "".join(parts)
    assert any("Next" in p for p in parts)


def test_output_controller_strips_markdown_and_caps_length() -> None:
    c = GuidanceOutputController(max_words=8, max_sentences=2)
    a = c.feed("### Opening: **Act** with care. ")
    b = c.feed("I hope this helps. Next line should be cut off soon.")
    text = (a + b).strip()
    assert "###" not in text
    assert "**" not in text
    assert "hope this helps" not in text.lower()
    assert len(text.split()) <= 8


def test_output_controller_polishes_short_citations_and_broken_phrase() -> None:
    c = GuidanceOutputController(max_words=60, max_sentences=4, allowed_citation_keys={"6.5", "2.47"})
    out = c.feed("Verse 5 applies here. A could be setting one tiny task.")
    assert out.strip()
    assert "###" not in out


def test_output_controller_fixes_oneself_do_not_and_gita_5() -> None:
    c = GuidanceOutputController(max_words=80, max_sentences=6, allowed_citation_keys={"6.5"})
    out = c.feed("Bhagavad Gita 5 says lift oneself do not degrade.")
    low = out.lower()
    assert "oneself; do not" in low or "oneself; do not" in out
    assert "6.5" in out


def test_polish_rewrites_citation_key_phrase_to_bhagavad_gita() -> None:
    raw = (
        "The line in citation key 2.47 speaks to releasing fixation on fruits. "
        "That fits your situation. Finish one task with care today. See 2.47."
    )
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"2.47"})
    assert "citation key" not in polished.lower()
    assert "Bhagavad Gita 2.47" in polished
    assert "See 2.47" not in polished


def test_polish_normalizes_ellipsis_before_see() -> None:
    raw = (
        "You can hold duty lightly without clutching every outcome … See 2.47."
    )
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"2.47"})
    assert "…" not in polished
    assert "See 2.47" not in polished
    assert polished.rstrip().endswith(".")


def test_polish_fixes_according_to_verse_advises() -> None:
    raw = (
        "According to Verse 2.47, advises steady action without clinging to results. "
        "According to Verse 6.5, the self can befriend itself with care. See 2.47."
    )
    polished = polish_guidance_full_text(
        raw,
        allowed_citation_keys={"2.47", "6.5"},
        primary_citation_key="2.47",
    )
    assert "According to Verse" not in polished
    # Structured-label contract: ``Verse 2.47`` is normalized to the canonical label.
    assert "Bhagavad Gita 2.47 advises" in polished
    assert "In Verse 6.5, the" in polished


def test_polish_fixes_the_bhagavad_gita_advises_without_citation() -> None:
    raw = "The Bhagavad Gita advises focusing on actions rather than obsessing over metrics (2.47)."
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"2.47"})
    assert "The Bhagavad Gita advises" not in polished
    assert "Bhagavad Gita 2.47 encourages" in polished


def test_polish_fixes_points_toward_in_citation_stack() -> None:
    raw = "Bhagavad Gita 6.5 points toward in 6.5 steady effort without harsh blame."
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"6.5"})
    assert "points toward in" not in polished.lower()
    assert "centers on 6.5" in polished.lower()


def test_polish_fixes_orphan_possessive_guidance_phrase() -> None:
    raw = "When days feel long, 's guidance in 2.47 still names duty without clinging to every outcome."
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"2.47"})
    assert "'s guidance in" not in polished
    assert "The guidance in Bhagavad Gita 2.47" in polished


def test_polish_fixes_leading_citation_then_reflect() -> None:
    raw = "Duty stays steady. 2.47 Reflect on effort without clinging to every scoreboard swing."
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"2.47"})
    assert "2.47 Reflect" not in polished
    assert "In Bhagavad Gita 2.47, reflect" in polished


def test_polish_fixes_a_is_setting_glitch() -> None:
    raw = "A is setting small boundaries before you reopen the metrics tab (2.47)."
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"2.47"})
    assert "A is setting" not in polished
    assert "The emphasis is on setting" in polished


def test_polish_fixes_encourages_to_lift_oneself() -> None:
    raw = "Bhagavad Gita 6.5 encourages to lift oneself without harsh self-blame."
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"6.5"})
    assert "encourages to lift" not in polished.lower()
    assert "encourages lifting oneself" in polished.lower()


def test_polish_fixes_word_as_advises_glitch() -> None:
    raw = "Small practice as advises against harsh self-blame when habits slip (6.5)."
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"6.5"})
    assert "practice advises" in polished.lower()
    assert " as advises" not in polished.lower()


def test_polish_fixes_the_bhagavad_gita_comma_advises() -> None:
    raw = "The Bhagavad Gita 2.47, advises steady action without clinging to results."
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"2.47"})
    assert "The Bhagavad Gita 2.47, advises" not in polished
    assert "Bhagavad Gita 2.47 advises" in polished


def test_polish_fixes_according_to_bhagavad_gita_advises() -> None:
    raw = (
        "According to Bhagavad Gita 2.47, advises steady action without clinging to results. "
        "According to Bhagavad Gita 6.5, the self can befriend itself with care. See 2.47."
    )
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"2.47", "6.5"})
    assert "According to Bhagavad Gita" not in polished
    assert "Bhagavad Gita 2.47 advises" in polished
    assert "In Bhagavad Gita 6.5, the" in polished


def test_polish_repairs_truncated_bhagavad_gita_using_primary_not_sort_order() -> None:
    raw = "Bhagavad Gita 6. lifts the self with care rather than harsh blame (6.5)."
    polished = polish_guidance_full_text(
        raw,
        allowed_citation_keys={"2.47", "6.5"},
        primary_citation_key="6.5",
    )
    assert "Bhagavad Gita 6. lifts" not in polished
    assert "Bhagavad Gita 6.5 lifts" in polished


def test_polish_strips_ending_with_small_concrete_next_step_rubric() -> None:
    raw = (
        "Verse 6.5 steadies effort without turning inward as an enemy. "
        "Ending with a small concrete next step: pause before the next harsh self-judgment."
    )
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"6.5"})
    assert "Ending with a small concrete next step" not in polished.lower()


def test_polish_repairs_in_chapter_dot_followed_by_text() -> None:
    raw = (
        "Your duty is to act without clinging to outcomes, as emphasized in 2.Focus on effort first."
    )
    polished = polish_guidance_full_text(
        raw,
        allowed_citation_keys={"2.47"},
        primary_citation_key="2.47",
    )
    assert "in 2.Focus" not in polished
    assert "in 2.47 Focus" in polished


def test_polish_adds_terminal_period_for_trailing_bare_citation() -> None:
    raw = "Verse 2.47 points to action without clinging. 2.47"
    polished = polish_guidance_full_text(raw, allowed_citation_keys={"2.47"})
    assert polished.endswith("2.47.")


def test_polish_repairs_bhagavad_gita_chapter_dot_fused_with_capital_word() -> None:
    """``Bhagavad Gita 2.This`` -> ``Bhagavad Gita 2.47 This`` (space inserted, not fused)."""
    raw = (
        "Your duty is to act without seeking control over the outcomes, as emphasized by "
        "Bhagavad Gita 2.This means focusing on your actions (Bhagavad Gita 2.47)."
    )
    polished = polish_guidance_full_text(
        raw,
        allowed_citation_keys={"2.47", "18.66"},
        primary_citation_key="2.47",
    )
    assert "Bhagavad Gita 2.47 This" in polished
    assert "Bhagavad Gita 2.This" not in polished
    assert not re.search(r"\bBhagavad\s+Gita\s+\d+\.[A-Z]", polished)


def test_polish_drops_sentence_leading_bare_citation_when_already_cited() -> None:
    """``. 6.5 A concrete...`` is cleaned to ``. A concrete...`` when ``6.5`` appears earlier."""
    raw = (
        "Bhagavad Gita 6.5 stresses lifting oneself through steady effort. "
        "6.5 A concrete next step could be setting small, manageable goals."
    )
    polished = polish_guidance_full_text(
        raw,
        allowed_citation_keys={"6.5", "18.66"},
        primary_citation_key="6.5",
    )
    assert "6.5 A concrete" not in polished
    assert ". A concrete next step" in polished
    assert "Bhagavad Gita 6.5" in polished


def test_polish_keeps_bare_citation_when_not_cited_earlier() -> None:
    """If the citation has not appeared before the sentence lead, keep it for salvage."""
    raw = "Duty matters. 2.47 Act without clinging to every outcome."
    polished = polish_guidance_full_text(
        raw,
        allowed_citation_keys={"2.47"},
        primary_citation_key="2.47",
    )
    assert "2.47" in polished


def test_polish_repairs_varied_connectors_with_chapter_only_citation() -> None:
    raws = [
        "The counsel at 2.Act first with steady effort.",
        "Guidance from 2. Act calmly today.",
        "According to Bhagavad Gita 2.Act, hold your duty lightly.",
    ]
    for raw in raws:
        polished = polish_guidance_full_text(
            raw,
            allowed_citation_keys={"2.47", "18.66"},
            primary_citation_key="2.47",
        )
        assert "2.47" in polished
        assert not re.search(r"\b2\.(?=[A-Z])", polished), polished
        assert not re.search(r"\b2\.\s+[A-Z]", polished), polished


def test_salvage_injects_primary_when_body_misses_it() -> None:
    body = (
        "Your duty is to act without clinging to outcomes. "
        "Focus on one bounded task you can finish today."
    )
    out = salvage_missing_primary_citation(body, primary_citation_key="2.47")
    assert "2.47" in out
    assert out.startswith(
        "Your duty is to act without clinging to outcomes (Bhagavad Gita 2.47)."
    )


def test_salvage_is_noop_when_primary_already_mentioned() -> None:
    body = "Bhagavad Gita 2.47 asks for right action without clinging to fruits."
    out = salvage_missing_primary_citation(body, primary_citation_key="2.47")
    assert out == body


def test_salvage_accepts_prose_form_as_already_mentioning_primary() -> None:
    body = "In chapter 2 verse 47, duty stays steady without owning every result."
    out = salvage_missing_primary_citation(body, primary_citation_key="2.47")
    assert out == body
