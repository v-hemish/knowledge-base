"""Run eval suite against a SQLite DB using the production retrieval pipeline."""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from pathlib import Path

from app.core.config import Settings
from app.evals.metrics import (
    EvalCaseResult,
    EvalMetricsSummary,
    case_result_from_run,
    compute_metrics,
)
from app.evals.schema import EvalCase, EvalSuiteFile, parse_eval_suite
from app.retrieval.pipeline import retrieve_verses_for_query

_log = logging.getLogger(__name__)


async def run_eval_case(
    conn: sqlite3.Connection,
    *,
    case: EvalCase,
    settings: Settings,
    top_k: int = 3,
) -> EvalCaseResult:
    verses = await retrieve_verses_for_query(conn, query=case.user_query, settings=settings)
    cites = tuple(v.citation_key for v in verses[:top_k])
    return case_result_from_run(
        case_id=case.id,
        user_query=case.user_query,
        retrieved_citations=cites,
        acceptable_citations=tuple(case.acceptable_citations),
        misleading_citations=tuple(case.misleading_citations),
        has_explanation_grade=case.explanation_grade is not None,
    )


async def run_suite(
    conn: sqlite3.Connection,
    *,
    suite: EvalSuiteFile,
    settings: Settings,
    top_k: int = 3,
) -> tuple[list[EvalCaseResult], EvalMetricsSummary]:
    results: list[EvalCaseResult] = []
    for case in suite.cases:
        r = await run_eval_case(conn, case=case, settings=settings, top_k=top_k)
        results.append(r)
        _log.debug("eval_case", extra={"id": r.case_id, "retrieved": list(r.retrieved_citations)})
    return results, compute_metrics(results)


def load_suite(path: Path) -> EvalSuiteFile:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return parse_eval_suite(raw)


def format_cli_summary(
    suite: EvalSuiteFile,
    metrics: EvalMetricsSummary,
    results: list[EvalCaseResult],
) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("Retrieval eval summary")
    lines.append("=" * 72)
    if suite.description:
        lines.append(suite.description.strip())
        lines.append("-" * 72)
    lines.append(f"Cases: {metrics.n_cases}")
    lines.append(f"  citation_hit_rate (mean acceptable recall@3): {metrics.citation_hit_rate:.4f}")
    lines.append(f"  top1_hit_rate:                              {metrics.top1_hit_rate:.4f}")
    lines.append(f"  top3_hit_rate:                              {metrics.top3_hit_rate:.4f}")
    lines.append(f"  misleading_retrieval_rate:                  {metrics.misleading_retrieval_rate:.4f}")
    lines.append(
        f"  explanation_grade_placeholder_rate:       {metrics.explanation_grade_placeholder_rate:.4f}"
    )
    lines.append("-" * 72)
    lines.append("Per-case (retrieved citations → flags)")
    lines.append("-" * 72)
    for r in results:
        flags = []
        if r.top1_hit:
            flags.append("top1✓")
        if r.top3_hit:
            flags.append("top3✓")
        if r.misleading_hit:
            flags.append("MISLEADING✗")
        flag_s = " ".join(flags) if flags else "—"
        lines.append(f"  {r.case_id}")
        lines.append(f"    query: {r.user_query[:76]}{'…' if len(r.user_query) > 76 else ''}")
        lines.append(f"    retrieved: {list(r.retrieved_citations) or '[]'}")
        lines.append(f"    acceptable_recall@k: {r.acceptable_recall_at_k:.3f}  {flag_s}")
    lines.append("=" * 72)
    return "\n".join(lines)
