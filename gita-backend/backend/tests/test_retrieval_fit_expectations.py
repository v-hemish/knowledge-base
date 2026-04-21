"""Theme-fit checks: retrieve → intent rank → explicit theme pins (same order as guidance)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.db.database import connect
from app.llm.query_intent import rank_verses_by_intent_and_fit
from app.llm.theme_routing import apply_theme_ordered_pins
from app.models.verse import Verse
from app.retrieval.pipeline import retrieve_verses_for_query

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_EXPECTATIONS_PATH = _BACKEND_ROOT / "data" / "retrieval_fit_expectations.json"
_DB_PATH = _BACKEND_ROOT / "data" / "gita.db"


def _passes(item: dict[str, object], ranked: list[Verse]) -> tuple[bool, str]:
    if not ranked:
        return False, "no verses retrieved"
    top = ranked[0]
    forb = set(item.get("forbidden_top1_citations") or ())
    if top.citation_key in forb:
        return False, f"forbidden top1 {top.citation_key}"
    acc = set(item.get("acceptable_top1_citations") or ())
    if top.citation_key in acc:
        return True, "top1 in expected theme family"
    pool = {v.citation_key for v in ranked}
    if pool & acc:
        return True, "expected theme verse in surfaced set (FTS may rank noise first)"
    return False, f"top1={top.citation_key} no theme family in surfaced set"


@pytest.mark.asyncio
async def test_retrieval_theme_fit_expectations_real_db(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _DB_PATH.is_file() or not _EXPECTATIONS_PATH.is_file():
        pytest.skip("gita.db or retrieval_fit_expectations.json not present")
    monkeypatch.setenv("DATABASE_PATH", str(_DB_PATH))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()
    settings = get_settings()
    conn = connect(_DB_PATH)
    items: list[dict[str, object]] = json.loads(_EXPECTATIONS_PATH.read_text(encoding="utf-8"))
    failures: list[tuple[str, str, str | None]] = []
    try:
        for item in items:
            q = str(item["query"])
            raw = await retrieve_verses_for_query(conn, query=q, settings=settings)
            ranked = rank_verses_by_intent_and_fit(q, raw)
            ranked = apply_theme_ordered_pins(q, ranked)
            if len(ranked) > settings.final_verse_count:
                ranked = ranked[: settings.final_verse_count]
            ok, reason = _passes(item, ranked)
            if not ok:
                top_key = ranked[0].citation_key if ranked else None
                failures.append((str(item["id"]), reason, top_key))
    finally:
        conn.close()
    assert not failures, "; ".join(f"{i}: {r} (top={t})" for i, r, t in failures)


def test_theme_pins_move_canonical_when_present() -> None:
    def v(key: str) -> Verse:
        ch, vs = key.split(".")
        return Verse.from_row(
            {
                "id": int(ch) * 100 + int(vs),
                "chapter": int(ch),
                "verse": int(vs),
                "citation_key": key,
                "translation": "x",
                "sanskrit": None,
                "transliteration": None,
                "theme_tags": [],
                "situation_tags": [],
                "use_with_care_tags": [],
                "translation_source": None,
            }
        )

    q = "I obsess over work metrics until I burn out"
    ranked = [v("1.22"), v("10.33"), v("2.47")]
    out = apply_theme_ordered_pins(q, ranked)
    assert out[0].citation_key == "2.47"
