"""Map ``gita_daily_practice_app_spec*.json`` ``starter_verse_pack`` rows to ``VerseInput``."""

from __future__ import annotations

from typing import Any

from app.schemas.verse_document import VerseInput


def _pack_item_to_verse(item: dict[str, Any]) -> VerseInput:
    ck = str(item.get("citation_key", "")).strip()
    if "." not in ck:
        raise ValueError(f"starter_verse_pack: missing or invalid citation_key: {item!r}")
    ch_s, v_s = ck.split(".", 1)
    chapter = int(ch_s)
    verse = int(v_s)
    trans = str(item.get("translation_plain", "")).strip()
    if not trans:
        raise ValueError(f"starter_verse_pack {ck}: translation_plain required")
    themes = item.get("theme")
    theme_tags = [str(t).strip() for t in themes] if isinstance(themes, list) else []
    theme_tags = [t for t in theme_tags if t]
    reflection = str(item.get("daily_reflection", "")).strip()
    tiny = str(item.get("tiny_practice", "")).strip()
    situation_tags = [reflection] if reflection else []
    use_tags = [tiny] if tiny else []
    return VerseInput(
        chapter=chapter,
        verse=verse,
        citation_key=ck,
        sanskrit=(str(item["sanskrit"]).strip() if item.get("sanskrit") else None) or None,
        transliteration=(str(item["transliteration"]).strip() if item.get("transliteration") else None) or None,
        translation=trans,
        theme_tags=theme_tags,
        situation_tags=situation_tags,
        use_with_care_tags=use_tags,
        translation_source="gita_daily_practice_app_spec_with_sanskrit.json",
    )


def verse_inputs_from_daily_practice_spec(raw: dict[str, Any]) -> list[VerseInput]:
    pack = raw.get("starter_verse_pack")
    if not isinstance(pack, list) or not pack:
        raise ValueError("daily practice spec: expected non-empty starter_verse_pack array")
    return [_pack_item_to_verse(dict(x)) for x in pack if isinstance(x, dict)]

