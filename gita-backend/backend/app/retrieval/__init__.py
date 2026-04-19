"""Retrieval subpackage: import from submodules (e.g. ``app.retrieval.pipeline``)."""

from app.retrieval.lexical import LexicalCandidate, lexical_search

# Do not import ``pipeline`` here — it pulls in ``app.services`` and creates a cycle
# when scripts import ``app.retrieval.embedding_artifact`` (e.g. ``embed_verses.py``).

__all__ = ["LexicalCandidate", "lexical_search"]
