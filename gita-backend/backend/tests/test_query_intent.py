from app.llm.query_intent import analyze_query, rank_verses_by_intent_and_fit, select_verses_for_generation
from app.models.verse import Verse


def _v(citation_key: str) -> Verse:
    ch, vs = citation_key.split(".")
    return Verse.from_row(
        {
            "id": int(ch) * 100 + int(vs),
            "chapter": int(ch),
            "verse": int(vs),
            "citation_key": citation_key,
            "translation": "x",
            "sanskrit": None,
            "transliteration": None,
            "theme_tags": [],
            "situation_tags": [],
            "use_with_care_tags": [],
            "translation_source": None,
        }
    )


def test_burnout_prioritizes_2_47() -> None:
    verses = [_v("6.5"), _v("2.47"), _v("18.66")]
    out = rank_verses_by_intent_and_fit("I obsess over work results and burn out", verses)
    assert out[0].citation_key == "2.47"


def test_discipline_prioritizes_6_5() -> None:
    verses = [_v("2.47"), _v("18.66"), _v("6.5")]
    out = rank_verses_by_intent_and_fit("How do I stop self-sabotage and build discipline?", verses)
    assert out[0].citation_key == "6.5"


def test_select_verses_respects_max_verses_with_preferred_order() -> None:
    """Burnout + max_verses=1 should pick exactly 1 verse (pre-existing off-by-one regression)."""
    verses = [_v("6.5"), _v("2.47"), _v("18.66")]
    picked = select_verses_for_generation(
        "My job never ends and I obsess over metrics until I feel burned out.",
        verses,
        max_verses=1,
    )
    assert len(picked) == 1
    assert picked[0].citation_key == "2.47"


def test_select_verses_respects_max_verses_when_no_preferred_order() -> None:
    verses = [_v("6.5"), _v("2.47"), _v("18.66")]
    picked = select_verses_for_generation("What does right action mean?", verses, max_verses=1)
    assert len(picked) == 1


def test_generation_pair_is_distinct() -> None:
    verses = [_v("6.5"), _v("2.47"), _v("18.66")]
    picked = select_verses_for_generation("moral obligations and fear of choosing wrong", verses, max_verses=2)
    keys = {v.citation_key for v in picked}
    assert len(keys) == len(picked)


def test_action_without_fruit_prefers_2_47_first() -> None:
    verses = [_v("6.5"), _v("2.47"), _v("18.66")]
    q = "I must act on my duty but cannot control how it will turn out"
    picked = select_verses_for_generation(q, verses, max_verses=2)
    assert picked[0].citation_key == "2.47"
    p = analyze_query(q)
    assert p.action_without_fruit is True


def test_surrender_prefers_18_66_first() -> None:
    verses = [_v("6.5"), _v("2.47"), _v("18.66")]
    q = "I want to surrender my fear and take refuge in grace"
    picked = select_verses_for_generation(q, verses, max_verses=2)
    assert picked[0].citation_key == "18.66"


def test_moral_conflict_does_not_route_18_66_without_explicit_surrender() -> None:
    verses = [_v("18.66"), _v("2.47"), _v("6.5")]
    q = "Two people I love expect opposite things from me; I fear making the wrong choice morally"
    picked = select_verses_for_generation(q, verses, max_verses=2)
    assert "18.66" not in {v.citation_key for v in picked}
    assert picked[0].citation_key == "2.47"


def test_discipline_prefers_6_5_over_2_47() -> None:
    verses = [_v("2.47"), _v("6.5"), _v("18.66")]
    q = "I struggle with discipline and self-sabotage whenever I try to build habits"
    picked = select_verses_for_generation(q, verses, max_verses=2)
    assert picked[0].citation_key == "6.5"
