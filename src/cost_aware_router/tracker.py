"""Cost tracker: spend vs single-model (all-premium) baseline.

Semantics (fixed in 0.1.1):

- ``by_tier`` counts **provider calls only** — cache hits are not
  routed calls and are never counted there.
- Quality is whatever the router *measured* with
  ``scoring.score_response`` and passed in; the tracker never invents
  a number. Gate-rejected calls are recorded too: they cost money.
- Cache hits record the premium counterfactual (baseline) but no
  spend and no quality.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from cost_aware_router.classifier import Tier
from cost_aware_router.models import ROUTING_TABLE


@dataclass
class CostTracker:
    """Accumulates routed spend and the all-premium counterfactual."""

    requests: int = 0
    cache_hits: int = 0
    spend_usd: float = 0.0
    baseline_usd: float = 0.0
    quality_sum: float = 0.0
    quality_count: int = 0
    by_tier: dict[str, int] = field(default_factory=dict)

    def record(self, tier: Tier, total_tokens: int, cached: bool = False,
               quality: float | None = None) -> None:
        """Record one event: a cache hit or a (paid) provider call."""
        premium = ROUTING_TABLE[Tier.PREMIUM]
        self.requests += 1
        self.baseline_usd += premium.price_per_1k_tokens * total_tokens / 1000
        if cached:
            self.cache_hits += 1
            return
        spec = ROUTING_TABLE[tier]
        self.spend_usd += spec.price_per_1k_tokens * total_tokens / 1000
        self.by_tier[str(tier)] = self.by_tier.get(str(tier), 0) + 1
        if quality is not None:
            self.quality_sum += quality
            self.quality_count += 1

    @property
    def saving_pct(self) -> float:
        """Percentage saved vs baseline."""
        return 0.0 if self.baseline_usd == 0 else round(
            100 * (1 - self.spend_usd / self.baseline_usd), 1)

    @property
    def avg_quality(self) -> float:
        """Mean *measured* quality over scored provider calls."""
        return 0.0 if self.quality_count == 0 else round(self.quality_sum / self.quality_count, 3)
