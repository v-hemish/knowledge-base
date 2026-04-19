import json
from pathlib import Path

import pytest

from app.evals.metrics import case_result_from_run, compute_metrics
from app.evals.runner import format_cli_summary, load_suite, run_suite
from app.evals.schema import EvalCase, EvalSuiteFile, parse_eval_suite


def test_parse_eval_suite_roundtrip() -> None:
    suite = EvalSuiteFile(
        schema_version=1,
        description="t",
        cases=[
            EvalCase(
                id="a",
                user_query="q",
                acceptable_citations=["2.47"],
                misleading_citations=["1.1"],
                notes="n",
            )
        ],
    )
    raw = json.loads(suite.model_dump_json())
    out = parse_eval_suite(raw)
    assert len(out.cases) == 1
    assert out.cases[0].id == "a"


def test_load_default_eval_cases_json() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "tests" / "fixtures" / "eval_cases.json"
    suite = load_suite(path)
    assert suite.schema_version == 1
    assert len(suite.cases) == 10
    ids = {c.id for c in suite.cases}
    assert "eval-001-grief" in ids
    assert "eval-010-family-tension" in ids


def test_compute_metrics_fixed_results() -> None:
    r1 = case_result_from_run(
        case_id="1",
        user_query="q",
        retrieved_citations=("2.47",),
        acceptable_citations=("2.47", "6.5"),
        misleading_citations=("18.66",),
        has_explanation_grade=False,
    )
    r2 = case_result_from_run(
        case_id="2",
        user_query="q2",
        retrieved_citations=("18.66",),
        acceptable_citations=("6.5",),
        misleading_citations=("18.66",),
        has_explanation_grade=True,
    )
    m = compute_metrics([r1, r2])
    assert m.n_cases == 2
    # r1 recall 0.5 (1 of 2 acceptable), r2 recall 0 (0 of 1) -> mean 0.25
    assert abs(m.citation_hit_rate - 0.25) < 1e-9
    assert m.top1_hit_rate == 0.5
    assert m.top3_hit_rate == 0.5
    assert m.misleading_retrieval_rate == 0.5
    assert m.explanation_grade_placeholder_rate == 0.5


def test_format_cli_summary_readable() -> None:
    suite = EvalSuiteFile(description="demo", cases=[])
    metrics = compute_metrics([])
    text = format_cli_summary(suite, metrics, [])
    assert "Retrieval eval summary" in text
    assert "citation_hit_rate" in text


@pytest.mark.asyncio
async def test_run_suite_smoke_on_seeded_db(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end eval run against a tiny DB (same pattern as other retrieval tests)."""
    from app.core.config import get_settings
    from app.db.database import connect, init_schema
    from app.db.ingestion import ingest_verse_inputs
    from app.db.session import make_engine, make_session_factory, session_scope
    from app.schemas.verse_document import VerseInput

    db = tmp_path / "eval.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_RERANK_ENABLED", "false")
    get_settings.cache_clear()

    init_schema(connect(db))
    engine = make_engine(db)
    with session_scope(make_session_factory(engine)) as session:
        ingest_verse_inputs(
            session,
            [
                VerseInput(
                    chapter=2,
                    verse=47,
                    citation_key="2.47",
                    translation="action fruits duty seed",
                    sanskrit=None,
                    transliteration=None,
                    theme_tags=["karma"],
                    situation_tags=[],
                    use_with_care_tags=[],
                ),
                VerseInput(
                    chapter=6,
                    verse=5,
                    citation_key="6.5",
                    translation="friend enemy self seed",
                    sanskrit=None,
                    transliteration=None,
                    theme_tags=[],
                    situation_tags=[],
                    use_with_care_tags=[],
                ),
            ],
        )

    suite = EvalSuiteFile(
        cases=[
            EvalCase(
                id="smoke-1",
                user_query="seed",
                acceptable_citations=["2.47", "6.5"],
                misleading_citations=[],
                notes="",
            )
        ],
    )
    settings = get_settings()
    conn = connect(settings.resolved_database_path())
    results, metrics = await run_suite(conn, suite=suite, settings=settings, top_k=3)
    conn.close()

    assert metrics.n_cases == 1
    assert results[0].retrieved_citations
    summary = format_cli_summary(suite, metrics, results)
    assert "smoke-1" in summary
    assert "citation_hit_rate" in summary
