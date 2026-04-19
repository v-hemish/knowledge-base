import pytest
from pydantic import ValidationError

from app.schemas.verse_document import CanonicalVerseFile, VerseInput, parse_canonical_verse_file_payload


def test_verse_input_accepts_valid_record() -> None:
    v = VerseInput(
        chapter=2,
        verse=47,
        citation_key="2.47",
        sanskrit="x",
        transliteration="y",
        translation="z",
        theme_tags=[" karma ", "karma", "duty"],
        situation_tags=[],
        use_with_care_tags=[],
    )
    assert v.theme_tags == ["karma", "duty"]


def test_verse_input_rejects_bad_citation_key_shape() -> None:
    with pytest.raises(ValidationError):
        VerseInput(
            chapter=2,
            verse=47,
            citation_key="II-47",
            translation="t",
        )


def test_verse_input_rejects_mismatched_citation_key() -> None:
    with pytest.raises(ValidationError):
        VerseInput(
            chapter=2,
            verse=47,
            citation_key="6.5",
            translation="t",
        )


def test_parse_canonical_file_accepts_object_or_array() -> None:
    doc = parse_canonical_verse_file_payload(
        {
            "verses": [
                {
                    "chapter": 1,
                    "verse": 1,
                    "citation_key": "1.1",
                    "translation": "t",
                    "theme_tags": [],
                    "situation_tags": [],
                    "use_with_care_tags": [],
                }
            ]
        }
    )
    assert isinstance(doc, CanonicalVerseFile)
    assert doc.verses[0].citation_key == "1.1"

    doc2 = parse_canonical_verse_file_payload(doc.verses)
    assert len(doc2.verses) == 1
