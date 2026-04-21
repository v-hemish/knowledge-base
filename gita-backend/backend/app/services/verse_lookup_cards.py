"""Build retrieve-shaped verse cards from DB rows (practice / direct lookup)."""

from __future__ import annotations

from app.models.verse import Verse
from app.schemas.guidance_retrieve import RetrieveVerseCard

_WHY_DIRECT = "Direct citation lookup (no full-text search)."


def verse_to_retrieve_card(verse: Verse) -> RetrieveVerseCard:
    return RetrieveVerseCard(
        citation_key=verse.citation_key,
        chapter=verse.chapter,
        verse=verse.verse,
        sanskrit=verse.sanskrit,
        transliteration=verse.transliteration,
        translation=verse.translation,
        why_selected_short=_WHY_DIRECT,
    )
