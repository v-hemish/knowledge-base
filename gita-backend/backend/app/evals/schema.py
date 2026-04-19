"""Pydantic models for hand-built eval cases (JSON on disk)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class EvalCase(BaseModel):
    """
    One labeled prompt for retrieval evaluation.

    `acceptable_citations` / `misleading_citations` use citation_key strings (e.g. "2.47").
    """

    id: str = Field(min_length=1, max_length=128)
    user_query: str = Field(min_length=1, max_length=4000)
    acceptable_citations: list[str] = Field(default_factory=list)
    misleading_citations: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=4000)

    # Placeholders for future manual explanation review (keep in JSON as null).
    explanation_grade: str | None = Field(default=None, max_length=32)
    manual_review_notes: str | None = Field(default=None, max_length=8000)

    @field_validator("acceptable_citations", "misleading_citations", mode="after")
    @classmethod
    def normalize_citations(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for x in v:
            s = str(x).strip()
            if not s or s in seen:
                continue
            seen.add(s)
            out.append(s)
        return out


class EvalSuiteFile(BaseModel):
    """Root object for on-disk eval suite JSON (default: tests/fixtures/eval_cases.json)."""

    schema_version: int = Field(default=1, ge=1)
    description: str = Field(default="", max_length=2000)
    cases: list[EvalCase] = Field(default_factory=list)


def parse_eval_suite(raw: object) -> EvalSuiteFile:
    """Accept a root object with `cases` or a bare list (wrapped as cases)."""
    if isinstance(raw, list):
        return EvalSuiteFile(cases=raw)
    if isinstance(raw, dict):
        return EvalSuiteFile.model_validate(raw)
    raise TypeError("eval suite JSON must be an object or array")
