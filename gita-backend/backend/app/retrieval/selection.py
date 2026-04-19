"""Retrieval selection: verse row plus deterministic metadata for answer assembly."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.verse import Verse


@dataclass(frozen=True, slots=True)
class VerseWithRetrievalMeta:
    """One selected verse with stage-1/stage-2 retrieval facts (no LLM)."""

    verse: Verse
    lexical_rank: int
    lexical_retrieval_score: float
    matched_by: tuple[str, ...]
    semantic_rerank_applied: bool
    final_position: int
    total_lexical_candidates: int
