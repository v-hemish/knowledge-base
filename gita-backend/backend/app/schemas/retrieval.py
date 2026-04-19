from pydantic import BaseModel, Field


class LexicalCandidateOut(BaseModel):
    verse_id: int
    chapter: int
    verse: int
    citation_key: str
    translation: str
    retrieval_score: float = Field(description="Higher is more relevant (negative of FTS5 bm25).")
    matched_by: list[str]
