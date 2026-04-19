from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping


def _parse_tag_json(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if not isinstance(raw, str) or not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [str(x) for x in data]


@dataclass(frozen=True, slots=True)
class Verse:
    """Canonical verse row assembled only from persistence — never from an LLM."""

    id: int
    chapter: int
    verse: int
    citation_key: str
    translation: str
    sanskrit: str | None
    transliteration: str | None
    theme_tags: list[str]
    situation_tags: list[str]
    use_with_care_tags: list[str]
    translation_source: str | None

    @property
    def citation(self) -> str:
        return f"Bhagavad Gita {self.citation_key}"

    def as_prompt_block(self) -> str:
        """Structured block injected into the model prompt (DB-sourced strings only)."""
        lines = [
            f"[{self.citation}]",
            f"Translation: {self.translation}",
        ]
        if self.transliteration:
            lines.append(f"Transliteration: {self.transliteration}")
        if self.sanskrit:
            lines.append(f"Sanskrit: {self.sanskrit}")
        if self.theme_tags:
            lines.append(f"Theme tags (DB): {', '.join(self.theme_tags)}")
        if self.situation_tags:
            lines.append(f"Situation tags (DB): {', '.join(self.situation_tags)}")
        if self.use_with_care_tags:
            lines.append(f"Use-with-care tags (DB): {', '.join(self.use_with_care_tags)}")
        return "\n".join(lines)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Verse:
        return cls(
            id=int(row["id"]),
            chapter=int(row["chapter"]),
            verse=int(row["verse"]),
            citation_key=str(row.get("citation_key") or f"{int(row['chapter'])}.{int(row['verse'])}"),
            translation=str(row["translation"]),
            sanskrit=row.get("sanskrit") if row.get("sanskrit") is not None else None,
            transliteration=row.get("transliteration") if row.get("transliteration") is not None else None,
            theme_tags=_parse_tag_json(row.get("theme_tags")),
            situation_tags=_parse_tag_json(row.get("situation_tags")),
            use_with_care_tags=_parse_tag_json(row.get("use_with_care_tags")),
            translation_source=row.get("translation_source") if row.get("translation_source") is not None else None,
        )
