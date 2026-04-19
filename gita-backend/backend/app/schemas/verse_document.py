"""Pydantic models for normalized on-disk verse JSON (source of truth before SQLite)."""

from __future__ import annotations

import json
import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

_CITATION_KEY_RE = re.compile(r"^\d+\.\d+$")


def _normalize_tag_list(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        t = raw.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


class VerseInput(BaseModel):
    """
    One verse record as ingested from canonical JSON.
    Tags are plain strings; persisted as JSON text in SQLite for simple querying.
    """

    chapter: int = Field(ge=1, le=18)
    verse: int = Field(ge=1, le=300)
    citation_key: str = Field(min_length=3, max_length=32)
    sanskrit: str | None = None
    transliteration: str | None = None
    translation: str = Field(min_length=1)
    theme_tags: list[str] = Field(default_factory=list)
    situation_tags: list[str] = Field(default_factory=list)
    use_with_care_tags: list[str] = Field(default_factory=list)
    translation_source: str | None = Field(
        default=None,
        description="Optional provenance; not required for canonical JSON.",
    )

    @field_validator("citation_key")
    @classmethod
    def citation_key_shape(cls, v: str) -> str:
        s = v.strip()
        if not _CITATION_KEY_RE.match(s):
            raise ValueError('citation_key must look like "2.47" (chapter.verse, ASCII digits)')
        return s

    @field_validator("theme_tags", "situation_tags", "use_with_care_tags", mode="before")
    @classmethod
    def coerce_tags(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
            except json.JSONDecodeError as exc:
                raise ValueError("tags must be a JSON array or list of strings") from exc
            if not isinstance(parsed, list):
                raise ValueError("tags JSON must be an array of strings")
            v = parsed
        if not isinstance(v, list):
            raise TypeError("tags must be a list")
        return [str(x).strip() for x in v if str(x).strip()]

    @field_validator("theme_tags", "situation_tags", "use_with_care_tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        return _normalize_tag_list(v)

    @model_validator(mode="after")
    def citation_key_matches_address(self) -> VerseInput:
        expected = f"{self.chapter}.{self.verse}"
        if self.citation_key != expected:
            raise ValueError(f'citation_key "{self.citation_key}" must equal "{expected}" for chapter/verse')
        return self


class CanonicalVerseFile(BaseModel):
    """Root object for a corpus file; also accepts a bare JSON array at load time."""

    verses: Annotated[list[VerseInput], Field(min_length=1)]


def parse_canonical_verse_file_payload(raw: object) -> CanonicalVerseFile:
    """Accept either `{"verses":[...]}` or a bare `[...]` list."""
    if isinstance(raw, list):
        return CanonicalVerseFile(verses=raw)
    if isinstance(raw, dict):
        return CanonicalVerseFile.model_validate(raw)
    raise TypeError("canonical verse JSON must be an object or array")
