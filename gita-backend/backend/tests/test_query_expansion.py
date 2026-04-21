from app.retrieval.query_expansion import expanded_retrieval_query


def test_expansion_empty_query() -> None:
    assert expanded_retrieval_query("") == ""
    assert expanded_retrieval_query("   ") == ""


def test_expansion_hedonic_adds_sense_discipline_terms() -> None:
    q = "I am addicted to porn what can I do"
    out = expanded_retrieval_query(q)
    assert out.startswith(q)
    assert "senses" in out
    assert "attachment" in out
    assert "self-mastery" in out


def test_expansion_addiction_only_milder_pack() -> None:
    q = "I cannot stop this habit and I feel out of control"
    out = expanded_retrieval_query(q)
    assert "habit" in out
    assert "steady" in out


def test_expansion_plain_question_unchanged() -> None:
    q = "What does Krishna say about duty without attachment?"
    assert expanded_retrieval_query(q) == q
