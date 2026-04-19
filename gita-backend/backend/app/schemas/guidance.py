from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class GuidanceFeedbackRequest(BaseModel):
    """Optional thumbs / notes after a guidance stream (logged only if GUIDANCE_FEEDBACK_LOG_PATH is set)."""

    rating: Literal["up", "down", "flag"]
    notes: str | None = Field(default=None, max_length=4000)
    client_stream_id: str | None = Field(
        default=None,
        max_length=128,
        description="Optional id from the client to correlate with its own session.",
    )


class GuidanceRequest(BaseModel):
    """User question for retrieval and/or streamed guidance."""

    query: str = Field(
        max_length=2000,
        description="Non-empty question after trim; max 2000 characters.",
    )
    eval_debug: bool = Field(
        default=False,
        description=(
            "When true, SSE `completed.eval` includes Ollama/stream diagnostics; failures are not masked "
            "with generic fallback text (set via JSON or GUIDANCE_EVAL_DEBUG)."
        ),
    )

    @field_validator("query")
    @classmethod
    def strip_and_validate_query(cls, value: str) -> str:
        s = value.strip()
        if not s:
            raise ValueError("query must not be empty")
        if len(s) > 2000:
            raise ValueError("query is too long")
        return s


class VerseCard(BaseModel):
    """API-facing verse payload — must mirror DB fields without reinterpretation."""

    chapter: int
    verse: int
    citation_key: str
    citation: str
    translation: str
    sanskrit: str | None = None
    transliteration: str | None = None
    theme_tags: list[str] = Field(default_factory=list)
    situation_tags: list[str] = Field(default_factory=list)
    use_with_care_tags: list[str] = Field(default_factory=list)
    translation_source: str | None = None


class GuidanceStreamEvent(BaseModel):
    """SSE JSON envelope (one JSON object per `data:` line)."""

    event: Literal["metadata", "verses", "token", "error", "completed"]
    data: dict[str, Any]
