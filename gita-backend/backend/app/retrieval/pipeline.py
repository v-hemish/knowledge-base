from __future__ import annotations

import logging
import sqlite3

from app.core.config import Settings
from app.models.verse import Verse
from app.services.retrieval_pipeline_service import RetrievalPipelineService

_log = logging.getLogger(__name__)

_pipeline = RetrievalPipelineService()


async def retrieve_verses_for_query(
    conn: sqlite3.Connection,
    *,
    query: str,
    settings: Settings,
) -> list[Verse]:
    """
    Lexical retrieval (FTS5) then optional semantic rerank; returns up to `final_verse_count`.
    FUTURE: chapter/verse filters, hybrid sparse+dense fusion.
    """
    return await _pipeline.retrieve(conn, query=query, settings=settings)
