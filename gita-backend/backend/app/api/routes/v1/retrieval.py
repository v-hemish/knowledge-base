import sqlite3

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db_conn, get_settings_dep
from app.core.config import Settings
from app.schemas.retrieval import LexicalCandidateOut
from app.services.lexical_retrieval_service import LexicalRetrievalService

router = APIRouter(tags=["retrieval"])


@router.get("/retrieval/lexical", response_model=list[LexicalCandidateOut])
def lexical_debug(
    q: str = Query("", max_length=2000, description="Search query (translation, transliteration, themes, situations)."),
    conn: sqlite3.Connection = Depends(get_db_conn),
    settings: Settings = Depends(get_settings_dep),
) -> list[LexicalCandidateOut]:
    """
    Debug: BM25-ranked lexical hits (FTS5).

    **Example**

    ``GET /api/v1/retrieval/lexical?q=duty``

    **Example item**

    ```json
    {
      "verse_id": 1,
      "chapter": 2,
      "verse": 47,
      "citation_key": "2.47",
      "translation": "...",
      "retrieval_score": 12.3,
      "matched_by": ["translation"]
    }
    ```

    FUTURE: auth-gate or remove outside dev.
    """
    svc = LexicalRetrievalService()
    hits = svc.search(conn, query=q, settings=settings)
    return [
        LexicalCandidateOut(
            verse_id=h.verse_id,
            chapter=h.chapter,
            verse=h.verse,
            citation_key=h.citation_key,
            translation=h.translation,
            retrieval_score=h.retrieval_score,
            matched_by=list(h.matched_by),
        )
        for h in hits
    ]
