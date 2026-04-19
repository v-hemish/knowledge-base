from app.llm.verse_framing import build_verse_framing, reorder_verses_by_fit
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


def test_build_verse_framing_penalizes_18_66_for_non_surrender_emotional_query() -> None:
    notes = build_verse_framing("I feel depressed and burned out at work results", [_v("18.66"), _v("2.47")])
    by_key = {n.citation_key: n for n in notes}
    assert by_key["2.47"].fit_score > by_key["18.66"].fit_score


def test_reorder_verses_by_fit_prioritizes_6_5_for_self_sabotage() -> None:
    verses = [_v("2.47"), _v("18.66"), _v("6.5")]
    out = reorder_verses_by_fit("self-sabotage and discipline", verses)
    assert out[0].citation_key == "6.5"
