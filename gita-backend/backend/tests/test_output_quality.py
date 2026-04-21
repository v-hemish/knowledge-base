"""Post-stream guidance quality helpers (truncation, citation tail)."""

from __future__ import annotations

from app.llm.output_quality import (
    citation_clarification_suffix,
    needs_completion_tail,
    trailing_see_citation_key,
)
from app.llm.query_intent import QueryProfile


def test_needs_completion_tail_open_without_punct() -> None:
    assert needs_completion_tail("You might try setting aside time for") is True


def test_needs_completion_tail_dangling_before_period() -> None:
    assert needs_completion_tail("Try an activity that brings.") is True


def test_needs_completion_tail_closed() -> None:
    assert needs_completion_tail("Try one small step today.") is False


def test_needs_completion_tail_allows_small_terminal_word() -> None:
    assert needs_completion_tail("No matter how small.") is False


def test_needs_completion_tail_question_complete() -> None:
    assert needs_completion_tail("What one boundary would make today easier?") is False


def test_trailing_see_citation_key() -> None:
    assert trailing_see_citation_key("…reflect. See 2.47.") == "2.47"
    assert trailing_see_citation_key("no see here") is None


def test_citation_clarification_burnout_mismatch() -> None:
    prof = QueryProfile(
        distress=False,
        burnout=True,
        discipline=False,
        moral_conflict=False,
        surrender_explicit=False,
        action_without_fruit=False,
        faith_grace_language=False,
        hedonic_compulsion=False,
        grief_regret=False,
        shame_past=False,
        comparison=False,
        spiritual_restart=False,
        effort_results=False,
        fear_of_failure=False,
        uncertain_outcome=False,
        invisible_effort=False,
        self_worth_from_achievement=False,
        gentle_discipline=False,
        comfort_over_duty=False,
    )
    text = "…metrics. See 6.5."
    s = citation_clarification_suffix(
        text,
        primary="2.47",
        allowed={"2.47", "6.5"},
        profile=prof,
    )
    assert s is not None
    assert "2.47" in s


def test_citation_clarification_skips_when_primary_matches() -> None:
    prof = QueryProfile(
        True,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    )
    assert (
        citation_clarification_suffix(
            "… See 2.47.",
            primary="2.47",
            allowed={"2.47", "6.5"},
            profile=prof,
        )
        is None
    )
