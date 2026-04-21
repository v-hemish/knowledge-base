from __future__ import annotations

import pytest

from app.retrieval.citation_query import citation_key_from_retrieval_query


@pytest.mark.parametrize(
    ("q", "expected"),
    [
        ("Bhagavad Gita 2.47", "2.47"),
        ("bhagavad gita 18.66", "18.66"),
        ("  6.5  ", "6.5"),
        ("Bhagavad Gita 2.47 and worry", "2.47"),
    ],
)
def test_citation_key_from_query(q: str, expected: str) -> None:
    assert citation_key_from_retrieval_query(q) == expected


def test_citation_key_rejects_thematic_question() -> None:
    assert citation_key_from_retrieval_query("I feel anxious about work") is None
