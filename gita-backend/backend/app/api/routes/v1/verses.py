"""Fast verse lookup by citation (practice UI); avoids full retrieval pipeline."""

from __future__ import annotations

import re
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import check_guidance_retrieve_rate_limit, get_db_conn, get_settings_dep
from app.core.config import Settings
from app.db.verses_repo import fetch_verses_by_citation_keys
from app.schemas.guidance_retrieve import RetrieveVerseCard
from app.schemas.verse_batch import CitationIndexResponse, VerseBatchKeysRequest, VerseBatchKeysResponse
from app.services.verse_lookup_cards import verse_to_retrieve_card
from app.utils.translation_quality import is_placeholder_translation

router = APIRouter(tags=["verses"])

_CITATION_KEY_RE = re.compile(r"^\d+\.\d+$")


@router.get("/verses/citation-index", response_model=CitationIndexResponse)
def get_citation_index(
    _rate_ok: None = Depends(check_guidance_retrieve_rate_limit),
    conn: sqlite3.Connection = Depends(get_db_conn),
    _settings: Settings = Depends(get_settings_dep),
) -> CitationIndexResponse:
    """
    All verses in canonical chapter/verse order, excluding rows with placeholder-only translations.
    Used by the Learn flashcard deck so the UI matches whatever is in SQLite (e.g. 701 slokas).
    """
    rows = conn.execute(
        "SELECT citation_key, translation FROM verses ORDER BY chapter, verse",
    ).fetchall()
    keys: list[str] = []
    for r in rows:
        if is_placeholder_translation(str(r["translation"])):
            continue
        keys.append(str(r["citation_key"]))
    return CitationIndexResponse(citation_keys=keys)


def _normalize_citation_key(raw: str) -> str:
    s = raw.strip()
    if not _CITATION_KEY_RE.match(s):
        raise HTTPException(
            status_code=422,
            detail={"message": 'citation_key must look like "2.47"', "citation_key": raw},
        )
    return s


def _try_normalize_citation_key(raw: str) -> str | None:
    s = raw.strip()
    return s if _CITATION_KEY_RE.match(s) else None


@router.get("/verses/by-key/{citation_key}", response_model=RetrieveVerseCard)
def get_verse_by_citation_key(
    citation_key: str,
    _rate_ok: None = Depends(check_guidance_retrieve_rate_limit),
    conn: sqlite3.Connection = Depends(get_db_conn),
    _settings: Settings = Depends(get_settings_dep),
) -> RetrieveVerseCard:
    ck = _normalize_citation_key(citation_key)
    rows = fetch_verses_by_citation_keys(conn, [ck])
    row = rows.get(ck)
    if row is None or is_placeholder_translation(row.translation):
        raise HTTPException(status_code=404, detail={"message": "Verse not found", "citation_key": ck})
    return verse_to_retrieve_card(row)


@router.post("/verses/by-keys", response_model=VerseBatchKeysResponse)
def post_verses_by_keys(
    body: VerseBatchKeysRequest,
    _rate_ok: None = Depends(check_guidance_retrieve_rate_limit),
    conn: sqlite3.Connection = Depends(get_db_conn),
    _settings: Settings = Depends(get_settings_dep),
) -> VerseBatchKeysResponse:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in body.citation_keys:
        ck = _try_normalize_citation_key(raw)
        if ck is None:
            continue
        if ck in seen:
            continue
        seen.add(ck)
        ordered.append(ck)
    if not ordered:
        return VerseBatchKeysResponse(verses={})
    rows = fetch_verses_by_citation_keys(conn, ordered)
    out: dict[str, RetrieveVerseCard] = {}
    for ck in ordered:
        v = rows.get(ck)
        if v is None or is_placeholder_translation(v.translation):
            continue
        out[ck] = verse_to_retrieve_card(v)
    return VerseBatchKeysResponse(verses=out)
