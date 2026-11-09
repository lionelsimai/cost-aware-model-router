"""Benchmark runner: unique golden cases, measured quality, honest spend.

Headline run: every case routed once, no repeats. Quality is scored
from the actual response text against the golden answer
(``scoring.score_response`` golden mode), for the routed router and
for an all-premium baseline. The cache is measured separately, in a
clearly labelled second scenario where the same traffic repeats.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from cost_aware_router.benchmark_data import ANSWER_BOOK, CASES
from cost_aware_router.classifier import Tier
from cost_aware_router.models import ROUTING_TABLE, estimate_tokens
from cost_aware_router.providers import MockProvider
from cost_aware_router.router import ModelRouter
from cost_aware_router.scoring import score_response


@dataclass
class BenchmarkReport:
    """Measured benchmark outcomes (no targets baked in)."""

    cases: int
    by_tier: dict[str, int] = field(default_factory=dict)
    routed_spend_usd: float = 0.0
    baseline_spend_usd: float = 0.0
    saving_pct: float = 0.0
    routed_quality: float = 0.0
    premium_quality: float = 0.0
    quality_drop_pct: float = 0.0
    per_case: list[dict[str, object]] = field(default_factory=list)
    cache_requests: int = 0
    cache_hits: int = 0
    cache_spend_usd: float = 0.0
    unique_spend_usd: float = 0.0


def _tokens(prompt: str) -> int:
    return estimate_tokens(prompt) + 60


def run_benchmark() -> BenchmarkReport:
    """Run the headline (unique) benchmark plus the cache scenario."""
    premium_spec = ROUTING_TABLE[Tier.PREMIUM]
    premium = MockProvider(premium_spec, answer_book=ANSWER_BOOK)
    router = ModelRouter(expected_answers=ANSWER_BOOK)

    routed_scores: list[float] = []
    premium_scores: list[float] = []
    baseline_spend = 0.0
    per_case: list[dict[str, object]] = []
    for case in CASES:
        result = router.route(case.prompt)
        routed_q = score_response(case.prompt, result.response, case.expected)
        premium_response = premium.complete(case.prompt)
        premium_q = score_response(case.prompt, premium_response, case.expected)
        routed_scores.append(routed_q)
        premium_scores.append(premium_q)
        baseline_spend += premium_spec.price_per_1k_tokens * _tokens(case.prompt) / 1000
        per_case.append({"kind": case.kind, "tier": str(result.tier),
                         "routed_quality": routed_q, "premium_quality": premium_q})

    tracker = router.tracker
    routed_quality = sum(routed_scores) / len(routed_scores)
    premium_quality = sum(premium_scores) / len(premium_scores)
    drop = 0.0 if premium_quality == 0 else 100 * (premium_quality - routed_quality) / premium_quality
    saving = 0.0 if baseline_spend == 0 else 100 * (1 - tracker.spend_usd / baseline_spend)

    # Cache scenario (separate, labelled): same unique traffic twice.
    cache_router = ModelRouter(expected_answers=ANSWER_BOOK)
    for case in CASES:
        cache_router.route(case.prompt)
    unique_spend = cache_router.tracker.spend_usd
    for case in CASES:
        cache_router.route(case.prompt)

    return BenchmarkReport(
        cases=len(CASES),
        by_tier=dict(tracker.by_tier),
        routed_spend_usd=tracker.spend_usd,
        baseline_spend_usd=baseline_spend,
        saving_pct=round(saving, 1),
        routed_quality=round(routed_quality, 3),
        premium_quality=round(premium_quality, 3),
        quality_drop_pct=round(drop, 1),
        per_case=per_case,
        cache_requests=cache_router.tracker.requests,
        cache_hits=cache_router.tracker.cache_hits,
        cache_spend_usd=cache_router.tracker.spend_usd,
        unique_spend_usd=unique_spend,
    )
