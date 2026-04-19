from app.llm.prompts import (
    GUIDANCE_SYSTEM_PROMPT,
    build_guidance_messages,
    build_guidance_user_message,
)
from app.models.verse import Verse


def _verse(**kwargs: object) -> Verse:
    base = {
        "id": 1,
        "chapter": 2,
        "verse": 47,
        "citation_key": "2.47",
        "translation": "EXACT_CANONICAL_TRANSLATION_X",
        "sanskrit": "SANSK_EXACT",
        "transliteration": "TRANS_EXACT",
        "theme_tags": [],
        "situation_tags": [],
        "use_with_care_tags": [],
        "translation_source": None,
    }
    base.update(kwargs)
    return Verse.from_row(base)


def test_guidance_system_prompt_constraints() -> None:
    low = GUIDANCE_SYSTEM_PROMPT.lower()
    assert "6.5" in low or "2.47" in low
    assert "krishna" in low
    assert "plain text" in low
    assert "72 words" in low
    assert "main verse" in low
    assert "scripture-first" in low


def test_build_guidance_user_message_embeds_exact_db_strings() -> None:
    v = _verse()
    user = build_guidance_user_message("What is duty?", [v], primary_citation_key="2.47")
    assert "EXACT_CANONICAL_TRANSLATION_X" in user
    assert "SANSK_EXACT" in user
    assert "TRANS_EXACT" in user
    assert "citation_key=2.47" in user
    assert "Hints (internal" in user
    assert user.count("EXACT_CANONICAL_TRANSLATION_X") == 1
    assert "MAIN verse" in user
    assert "Include token" in user
    assert "grammatical verse references only" in user
    assert "varied opening" in user.lower() or "teaches" in user.lower()
    assert "If you cite" in user


def test_build_guidance_messages_structure() -> None:
    v = _verse()
    msgs = build_guidance_messages(query="Why this verse?", verses=[v])
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    assert msgs[0]["content"] == GUIDANCE_SYSTEM_PROMPT
    assert "Why this verse?" in msgs[1]["content"]


def test_build_guidance_user_message_adds_grief_addon_after_loss_query() -> None:
    v = _verse()
    user = build_guidance_user_message(
        "After a loss I feel numb and replay what I should have done.",
        [v],
        primary_citation_key="2.47",
        distress=True,
    )
    assert "Grief/loss note" in user
    assert "chain discipline" in user.lower()


def test_prompt_build_does_not_mutate_verse_row() -> None:
    v = _verse()
    before = v.translation
    build_guidance_messages(query="q", verses=[v])
    assert v.translation == before
