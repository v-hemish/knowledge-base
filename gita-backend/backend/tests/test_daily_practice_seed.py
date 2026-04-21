from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas.daily_practice_seed import verse_inputs_from_daily_practice_spec


def _spec_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "gita_daily_practice_app_spec_with_sanskrit.json"


def test_daily_practice_spec_maps_starter_pack() -> None:
    path = _spec_path()
    if not path.is_file():
        pytest.skip(f"missing {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    verses = verse_inputs_from_daily_practice_spec(raw)
    assert len(verses) >= 1
    v0 = verses[0]
    assert v0.citation_key == f"{v0.chapter}.{v0.verse}"
    assert v0.translation
    assert v0.translation_source == "gita_daily_practice_app_spec_with_sanskrit.json"
