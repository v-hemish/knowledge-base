from app.llm.query_intent import (
    analyze_query,
    rank_verses_by_intent_and_fit,
    select_verses_for_generation,
    wants_two_verse_generation,
)
from app.llm.theme_routing import apply_theme_ordered_pins
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


def _rank_pin(q: str, verses: list[Verse]) -> list[Verse]:
    return apply_theme_ordered_pins(q, rank_verses_by_intent_and_fit(q, verses))


def test_effort_results_profile_without_burnout_keyword() -> None:
    p = analyze_query("I work hard but feel crushed when results do not match my effort.")
    assert p.effort_results is True


def test_effort_results_work_payoff_window() -> None:
    p = analyze_query("I cannot stop measuring my work by whether it pays off.")
    assert p.effort_results is True


def test_burned_out_matches_burnout() -> None:
    p = analyze_query("I feel burned out at work.")
    assert p.burnout is True


def test_discipline_delaying_and_sabotage_phrases() -> None:
    assert analyze_query("I keep delaying hard tasks every day.").discipline is True
    assert analyze_query("I keep sabotaging my own progress when I try new habits.").discipline is True


def test_new_practical_intent_buckets() -> None:
    u = analyze_query("I do my best, but I cannot control what happens next.")
    assert u.uncertain_outcome is True
    f = analyze_query("I am afraid to act because I might fail.")
    assert f.fear_of_failure is True
    g = analyze_query("How do I become more disciplined without becoming harsh with myself?")
    assert g.gentle_discipline is True
    c = analyze_query("I keep choosing comfort over what I know is right.")
    assert c.comfort_over_duty is True
    inv = analyze_query("My work feels thankless and invisible to others.")
    assert inv.invisible_effort is True
    sw = analyze_query("My self-worth rises and falls with achievement at school.")
    assert sw.self_worth_from_achievement is True


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
    q = "My job never ends and I obsess over metrics until I feel burned out."
    picked = select_verses_for_generation(q, _rank_pin(q, verses), max_verses=1)
    assert len(picked) == 1
    assert picked[0].citation_key == "2.47"


def test_select_verses_respects_max_verses_when_no_preferred_order() -> None:
    verses = [_v("6.5"), _v("2.47"), _v("18.66")]
    q = "What does right action mean?"
    picked = select_verses_for_generation(q, _rank_pin(q, verses), max_verses=1)
    assert len(picked) == 1


def test_generation_pair_is_distinct() -> None:
    verses = [_v("6.5"), _v("2.47"), _v("18.66")]
    q = "moral obligations and fear of choosing wrong"
    picked = select_verses_for_generation(q, _rank_pin(q, verses), max_verses=2)
    keys = {v.citation_key for v in picked}
    assert len(keys) == len(picked)


def test_action_without_fruit_prefers_2_47_first() -> None:
    verses = [_v("6.5"), _v("2.47"), _v("18.66")]
    q = "I must act on my duty but cannot control how it will turn out"
    picked = select_verses_for_generation(q, _rank_pin(q, verses), max_verses=2)
    assert picked[0].citation_key == "2.47"
    p = analyze_query(q)
    assert p.action_without_fruit is True


def test_surrender_prefers_18_66_first() -> None:
    verses = [_v("6.5"), _v("2.47"), _v("18.66")]
    q = "I want to surrender my fear and take refuge in grace"
    picked = select_verses_for_generation(q, _rank_pin(q, verses), max_verses=2)
    assert picked[0].citation_key == "18.66"


def test_moral_conflict_does_not_route_18_66_without_explicit_surrender() -> None:
    verses = [_v("18.66"), _v("2.47"), _v("6.5")]
    q = "Two people I love expect opposite things from me; I fear making the wrong choice morally"
    picked = select_verses_for_generation(q, _rank_pin(q, verses), max_verses=2)
    assert "18.66" not in {v.citation_key for v in picked}
    assert picked[0].citation_key == "2.47"


def test_discipline_prefers_6_5_over_2_47() -> None:
    verses = [_v("2.47"), _v("6.5"), _v("18.66")]
    q = "I struggle with discipline and self-sabotage whenever I try to build habits"
    picked = select_verses_for_generation(q, _rank_pin(q, verses), max_verses=2)
    assert picked[0].citation_key == "6.5"


def test_analyze_query_hedonic_compulsion() -> None:
    p = analyze_query("hooked on porn and cannot stop")
    assert p.hedonic_compulsion is True
    p2 = analyze_query("what is karma yoga")
    assert p2.hedonic_compulsion is False


def test_grief_regret_profile() -> None:
    p = analyze_query("After a loss I replay what I should have done")
    assert p.grief_regret is True
    assert p.shame_past is False


def test_shame_past_profile() -> None:
    p = analyze_query("I feel deep shame and regret over my past actions")
    assert p.shame_past is True
    assert p.grief_regret is False


def test_comparison_profile() -> None:
    p = analyze_query("I keep comparing myself and feel envy when others are ahead")
    assert p.comparison is True


def test_spiritual_restart_profile() -> None:
    p = analyze_query("I feel spiritually disconnected and want to begin again with God")
    assert p.spiritual_restart is True


def test_wants_two_verse_generation_phrases() -> None:
    assert wants_two_verse_generation("Please cite two verses on duty")
    assert wants_two_verse_generation("I need a deeper answer with more texture")
    assert wants_two_verse_generation("pair of verses about fear")
    assert not wants_two_verse_generation("What does verse 2.47 mean?")
