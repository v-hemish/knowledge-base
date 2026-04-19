"""Aggregate metrics from per-case retrieval eval results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvalCaseResult:
    case_id: str
    user_query: str
    retrieved_citations: tuple[str, ...]  # top-k order, citation_key
    acceptable_citations: tuple[str, ...]
    misleading_citations: tuple[str, ...]
    # Fraction of acceptable citations that appear in top-k for this case (0..1).
    acceptable_recall_at_k: float
    top1_hit: bool
    top3_hit: bool
    misleading_hit: bool
    has_explanation_grade: bool


@dataclass(frozen=True, slots=True)
class EvalMetricsSummary:
    n_cases: int
    citation_hit_rate: float
    top1_hit_rate: float
    top3_hit_rate: float
    misleading_retrieval_rate: float
    explanation_grade_placeholder_rate: float


def _safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def compute_metrics(results: list[EvalCaseResult]) -> EvalMetricsSummary:
    """
    - citation_hit_rate: mean per-case recall — |retrieved ∩ acceptable| / max(|acceptable|, 1)
    - top1_hit_rate: share of cases where rank-1 citation is acceptable
    - top3_hit_rate: share of cases where any top-3 citation is acceptable
    - misleading_retrieval_rate: share of cases where any top-3 citation is in misleading set
    """
    n = len(results)
    if n == 0:
        return EvalMetricsSummary(
            n_cases=0,
            citation_hit_rate=0.0,
            top1_hit_rate=0.0,
            top3_hit_rate=0.0,
            misleading_retrieval_rate=0.0,
            explanation_grade_placeholder_rate=0.0,
        )

    recalls: list[float] = []
    top1_hits = 0
    top3_hits = 0
    misleading_hits = 0
    graded = 0

    for r in results:
        if r.has_explanation_grade:
            graded += 1
        acc = set(r.acceptable_citations)
        mis = set(r.misleading_citations)
        ret = set(r.retrieved_citations)
        denom = max(len(acc), 1)
        recalls.append(len(ret & acc) / denom)
        if r.retrieved_citations:
            if r.retrieved_citations[0] in acc:
                top1_hits += 1
        if ret & acc:
            top3_hits += 1
        if ret & mis:
            misleading_hits += 1

    return EvalMetricsSummary(
        n_cases=n,
        citation_hit_rate=_safe_mean(recalls),
        top1_hit_rate=top1_hits / n,
        top3_hit_rate=top3_hits / n,
        misleading_retrieval_rate=misleading_hits / n,
        explanation_grade_placeholder_rate=graded / n,
    )


def case_result_from_run(
    *,
    case_id: str,
    user_query: str,
    retrieved_citations: tuple[str, ...],
    acceptable_citations: tuple[str, ...],
    misleading_citations: tuple[str, ...],
    has_explanation_grade: bool,
) -> EvalCaseResult:
    """Pure helper for tests (same logic as `runner.run_eval_case` post-retrieval)."""
    acc_set = set(acceptable_citations)
    mis_set = set(misleading_citations)
    ret_set = set(retrieved_citations)
    denom = max(len(acc_set), 1)
    recall = len(ret_set & acc_set) / denom
    top1 = bool(retrieved_citations and retrieved_citations[0] in acc_set)
    top3 = bool(ret_set & acc_set)
    bad = bool(ret_set & mis_set)
    return EvalCaseResult(
        case_id=case_id,
        user_query=user_query,
        retrieved_citations=retrieved_citations,
        acceptable_citations=acceptable_citations,
        misleading_citations=misleading_citations,
        acceptable_recall_at_k=recall,
        top1_hit=top1,
        top3_hit=top3,
        misleading_hit=bad,
        has_explanation_grade=has_explanation_grade,
    )
