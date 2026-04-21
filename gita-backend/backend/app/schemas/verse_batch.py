from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.guidance_retrieve import RetrieveVerseCard


class VerseBatchKeysRequest(BaseModel):
    citation_keys: list[str] = Field(min_length=1, max_length=64)


class VerseBatchKeysResponse(BaseModel):
    """Only keys with a non-placeholder row in SQLite are present."""

    verses: dict[str, RetrieveVerseCard]


class CitationIndexResponse(BaseModel):
    """Ordered ``citation_key`` list for Learn / full-corpus navigation (chapter, verse)."""

    citation_keys: list[str]
