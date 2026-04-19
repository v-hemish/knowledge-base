"""Canonical passage text used for verse embeddings (must match embed script)."""

from __future__ import annotations

from app.models.verse import Verse


def passage_for_embedding(verse: Verse) -> str:
    """Dense text for embedding: translation, transliteration, Sanskrit, tags."""
    tags = " ".join(verse.theme_tags + verse.situation_tags + verse.use_with_care_tags)
    parts = [
        verse.translation,
        verse.transliteration or "",
        verse.sanskrit or "",
        tags,
    ]
    return "\n".join(p for p in parts if p).strip()
