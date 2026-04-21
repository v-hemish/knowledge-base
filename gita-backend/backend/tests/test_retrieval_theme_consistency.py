"""Paraphrase groups should land in the same canonical theme family (real DB, optional)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import get_settings
from app.db.database import connect
from app.llm.query_intent import rank_verses_by_intent_and_fit
from app.llm.theme_routing import (
    CANONICAL_COMFORT_DUTY_FAMILY,
    CANONICAL_DISCIPLINE_FAMILY,
    CANONICAL_EFFORT_FAMILY,
    CANONICAL_FEAR_FAILURE_FAMILY,
    CANONICAL_GENTLE_DISCIPLINE_FAMILY,
    apply_theme_ordered_pins,
)
from app.retrieval.pipeline import retrieve_verses_for_query

_DB = Path(__file__).resolve().parents[1] / "data" / "gita.db"


async def _surfaced_top3(conn, settings, q: str) -> list[str]:
    raw = await retrieve_verses_for_query(conn, query=q, settings=settings)
    ranked = rank_verses_by_intent_and_fit(q, raw)
    pinned = apply_theme_ordered_pins(q, ranked)
    cap = pinned[: settings.final_verse_count]
    return [v.citation_key for v in cap[:3]]


def _family_hit(keys: list[str], family: frozenset[str]) -> bool:
    return bool(set(keys) & family)


@pytest.mark.asyncio
async def test_effort_paraphrases_share_canonical_family(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _DB.is_file():
        pytest.skip("gita.db not present")
    monkeypatch.setenv("DATABASE_PATH", str(_DB))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()
    settings = get_settings()
    conn = connect(_DB)
    paraphrases = [
        "I work hard but feel crushed when results do not match my effort.",
        "I obsess over performance metrics and feel burned out at work.",
        "I keep tying my self-worth to outcomes at my job.",
        "I cannot stop measuring my work by whether it pays off.",
    ]
    try:
        for q in paraphrases:
            top3 = await _surfaced_top3(conn, settings, q)
            assert _family_hit(top3, CANONICAL_EFFORT_FAMILY), (
                f"expected effort family in top-3 for {q!r}, got {top3}"
            )
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_discipline_paraphrases_share_canonical_family(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _DB.is_file():
        pytest.skip("gita.db not present")
    monkeypatch.setenv("DATABASE_PATH", str(_DB))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()
    settings = get_settings()
    conn = connect(_DB)
    paraphrases = [
        "I keep procrastinating and then hating myself for it. How do I build discipline?",
        "I know what I should do but I keep delaying it every day.",
        "I keep sabotaging my own progress when I try new habits.",
        "My mind wanders toward comfort; how do I train discipline without harshness?",
    ]
    try:
        for q in paraphrases:
            top3 = await _surfaced_top3(conn, settings, q)
            assert _family_hit(top3, CANONICAL_DISCIPLINE_FAMILY), (
                f"expected discipline family in top-3 for {q!r}, got {top3}"
            )
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_uncertain_outcome_paraphrases_share_effort_family(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _DB.is_file():
        pytest.skip("gita.db not present")
    monkeypatch.setenv("DATABASE_PATH", str(_DB))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()
    settings = get_settings()
    conn = connect(_DB)
    paraphrases = [
        "I do my best, but I cannot control what happens next.",
        "It is not up to me how things turn out after I have acted.",
        "I have no control over what happens next, only over my effort today.",
    ]
    try:
        for q in paraphrases:
            top3 = await _surfaced_top3(conn, settings, q)
            assert _family_hit(top3, CANONICAL_EFFORT_FAMILY), (
                f"expected effort family in top-3 for {q!r}, got {top3}"
            )
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_fear_of_failure_paraphrases_share_family(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _DB.is_file():
        pytest.skip("gita.db not present")
    monkeypatch.setenv("DATABASE_PATH", str(_DB))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()
    settings = get_settings()
    conn = connect(_DB)
    paraphrases = [
        "I am afraid to act because I might fail.",
        "I keep avoiding action because I fear failing in front of others.",
        "I am scared to try in case I fail publicly.",
    ]
    try:
        for q in paraphrases:
            top3 = await _surfaced_top3(conn, settings, q)
            assert _family_hit(top3, CANONICAL_FEAR_FAILURE_FAMILY), (
                f"expected fear/act family in top-3 for {q!r}, got {top3}"
            )
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_gentle_discipline_paraphrases_share_family(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _DB.is_file():
        pytest.skip("gita.db not present")
    monkeypatch.setenv("DATABASE_PATH", str(_DB))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()
    settings = get_settings()
    conn = connect(_DB)
    paraphrases = [
        "How do I become more disciplined without becoming harsh with myself?",
        "I want steadier habits but I do not want to be cruel to myself.",
        "Can I train discipline gently, without turning into my own harsh critic?",
    ]
    try:
        for q in paraphrases:
            top3 = await _surfaced_top3(conn, settings, q)
            assert _family_hit(top3, CANONICAL_GENTLE_DISCIPLINE_FAMILY), (
                f"expected gentle discipline family in top-3 for {q!r}, got {top3}"
            )
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_comfort_over_duty_paraphrases_share_family(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _DB.is_file():
        pytest.skip("gita.db not present")
    monkeypatch.setenv("DATABASE_PATH", str(_DB))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()
    settings = get_settings()
    conn = connect(_DB)
    paraphrases = [
        "I keep choosing comfort over what I know is right.",
        "I take the easy path instead of doing what I know I should do.",
        "Short-term comfort keeps winning over what I know is right.",
    ]
    try:
        for q in paraphrases:
            top3 = await _surfaced_top3(conn, settings, q)
            assert _family_hit(top3, CANONICAL_COMFORT_DUTY_FAMILY), (
                f"expected comfort/duty family in top-3 for {q!r}, got {top3}"
            )
    finally:
        conn.close()
