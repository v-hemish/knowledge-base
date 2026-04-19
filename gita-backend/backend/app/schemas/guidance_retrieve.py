from typing import Annotated, Literal

from pydantic import BaseModel, Field

ExplanationStatus = Literal["verses_only", "no_hits"]


class RetrieveVerseCard(BaseModel):
    """Verse payload for non-streaming retrieve; text fields are DB-sourced only."""

    citation_key: str
    chapter: int
    verse: int
    sanskrit: str | None = None
    transliteration: str | None = None
    translation: str
    why_selected_short: str = Field(
        ...,
        description="Deterministic summary from retrieval metadata (not from an LLM).",
    )


class RetrieveGuidanceResponse(BaseModel):
    """Verse cards first; no generated explanation in this response."""

    query: str
    selected_verses: Annotated[list[RetrieveVerseCard], Field(max_length=3)]
    reflection_prompt: str | None = Field(
        default=None,
        description="Optional hint for a follow-up explanation request.",
    )
    explanation_status: ExplanationStatus
