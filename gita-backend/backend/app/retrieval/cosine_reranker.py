"""
Second-stage semantic reranking: cosine similarity using precomputed verse embeddings.

Query side uses the same sentence-transformers model name as the artifact; for BGE
models we apply the standard asymmetric query instruction when encoding the user query.
"""

from __future__ import annotations

import logging
import threading

import numpy as np

from app.core.config import Settings
from app.llm.query_intent import analyze_query, intent_boost_for_citation
from app.models.verse import Verse
from app.retrieval.embedding_store import VerseEmbeddingIndex

_log = logging.getLogger(__name__)

_model_lock = threading.Lock()
_query_model: object | None = None
_query_model_name: str | None = None


def _get_query_model(model_name: str):
    global _query_model, _query_model_name
    from sentence_transformers import SentenceTransformer

    with _model_lock:
        if _query_model is None or _query_model_name != model_name:
            _log.info("loading_query_encoder", extra={"model": model_name})
            _query_model = SentenceTransformer(model_name)
            _query_model_name = model_name
        return _query_model


def encode_query_vector(model_name: str, query: str) -> np.ndarray:
    """Encode user query; L2-normalized vector (float32, D)."""
    model = _get_query_model(model_name)
    q = query.strip()
    if not q:
        raise ValueError("empty query")
    prefix = ""
    if "bge" in model_name.lower():
        prefix = "Represent this sentence for searching relevant passages: "
    emb = model.encode(
        [prefix + q],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    out = np.asarray(emb[0], dtype=np.float32)
    n = float(np.linalg.norm(out)) + 1e-12
    out /= n
    return out


def order_verses_by_cosine(
    query_vec: np.ndarray,
    verses: list[Verse],
    index: VerseEmbeddingIndex,
    *,
    intent_boosts: np.ndarray | None = None,
    intent_lambda: float = 0.0,
) -> list[Verse]:
    """
    Pure cosine rerank (normalized embeddings): higher dot product = more similar.
    Optional small intent blend breaks ties when cosine scores are close (small corpora).

    Caller must ensure every verse.id exists in the index.
    """
    if len(verses) <= 1:
        return verses
    ids = [v.id for v in verses]
    mat = index.row_matrix_for(ids).astype(np.float32, copy=False)
    q = np.asarray(query_vec, dtype=np.float32).reshape(-1)
    sims = np.asarray(mat @ q, dtype=np.float32).reshape(-1)
    if intent_boosts is not None and intent_lambda > 0.0:
        ib = np.asarray(intent_boosts, dtype=np.float32).reshape(-1)
        if ib.shape == sims.shape:
            scale = float(np.max(np.abs(ib)) + 1e-6)
            sims = sims + np.float32(intent_lambda) * (ib / scale)
    order = list(np.argsort(-sims))
    return [verses[i] for i in order]


def rerank_with_index(
    query: str,
    verses: list[Verse],
    *,
    settings: Settings,
    index: VerseEmbeddingIndex,
) -> list[Verse]:
    """
    Rerank lexical candidates by semantic similarity. If anything is inconsistent,
    returns `verses` unchanged (lexical order).
    """
    if len(verses) <= 1:
        return verses
    if index.model_name != settings.embedding_model:
        _log.warning(
            "embedding_model_mismatch",
            extra={"artifact_model": index.model_name, "settings_model": settings.embedding_model},
        )
        return verses
    ids = [v.id for v in verses]
    if not index.has_all(ids):
        _log.warning("embedding_rows_missing_for_candidates", extra={"verse_ids": ids})
        return verses
    try:
        qv = encode_query_vector(settings.embedding_model, query)
    except Exception:
        _log.exception("query_encode_failed")
        return verses
    if qv.shape[0] != index.embedding_dim:
        _log.warning(
            "embedding_dim_mismatch",
            extra={"query_dim": int(qv.shape[0]), "index_dim": index.embedding_dim},
        )
        return verses
    profile = analyze_query(query)
    boosts = np.array(
        [float(intent_boost_for_citation(profile, v.citation_key)) for v in verses],
        dtype=np.float32,
    )
    # Cosine remains dominant; intent nudges ordering when similarities cluster (few verses).
    return order_verses_by_cosine(
        qv,
        verses,
        index,
        intent_boosts=boosts,
        intent_lambda=0.28,
    )
