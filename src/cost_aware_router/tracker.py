"""Cost tracker: spend vs single-model (all-premium) baseline."""
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
    by_tier: dict[str, int] = field(default_factory=dict)

    def record(self, tier: Tier, total_tokens: int, cached: bool = False) -> None:
        """Record one request."""
        spec = ROUTING_TABLE[tier]
        premium = ROUTING_TABLE[Tier.PREMIUM]
        self.requests += 1
        self.baseline_usd += premium.price_per_1k_tokens * total_tokens / 1000
        self.by_tier[str(tier)] = self.by_tier.get(str(tier), 0) + 1
        if cached:
            self.cache_hits += 1
        else:
            self.spend_usd += spec.price_per_1k_tokens * total_tokens / 1000
            self.quality_sum += spec.quality

    @property
    def saving_pct(self) -> float:
        """Percentage saved vs baseline."""
        return 0.0 if self.baseline_usd == 0 else round(100 * (1 - self.spend_usd / self.baseline_usd), 1)

    @property
    def avg_quality(self) -> float:
        """Mean quality of non-cached routed responses."""
        n = self.requests - self.cache_hits
        return 0.0 if n == 0 else round(self.quality_sum / n, 3)
