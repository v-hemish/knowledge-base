import pytest

from app.core.config import get_settings
from app.schemas.verse_document import VerseInput


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _fast_guidance_stream_pacing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid real-time sleeps in guidance stream tests (production default remains in Settings)."""
    monkeypatch.setenv("GUIDANCE_STREAM_CHUNK_DELAY_S", "0")
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _clear_embedding_index() -> None:
    from app.retrieval.embedding_store import set_embedding_index

    set_embedding_index(None)
    yield
    set_embedding_index(None)


@pytest.fixture(autouse=True)
def _reset_guidance_rate_limiter() -> None:
    from app.core.rate_limit import guidance_rate_limiter, guidance_retrieve_rate_limiter

    guidance_rate_limiter().reset()
    guidance_retrieve_rate_limiter().reset()
    yield
    guidance_rate_limiter().reset()
    guidance_retrieve_rate_limiter().reset()


@pytest.fixture(autouse=True)
def _clear_retrieve_cache() -> None:
    from app.services.retrieve_cache import retrieve_cache_clear

    retrieve_cache_clear()
    yield
    retrieve_cache_clear()


@pytest.fixture
def make_verse_input():
    def _make(**kwargs: object) -> VerseInput:
        base: dict[str, object] = {
            "chapter": 2,
            "verse": 47,
            "citation_key": "2.47",
            "translation": "distincttoken action fruits",
            "sanskrit": None,
            "transliteration": None,
            "theme_tags": [],
            "situation_tags": [],
            "use_with_care_tags": [],
            "translation_source": "test",
        }
        base.update(kwargs)
        return VerseInput(**base)

    return _make
