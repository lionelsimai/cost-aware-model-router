"""Routing table: tiers, mock models, prices ($ per 1k tokens).

Prices are illustrative mock prices in the shape of real
mini/standard/frontier spreads — re-price from your provider's
current price page before quoting any saving externally.

Note (0.1.1): ``ModelSpec`` no longer carries a ``quality`` constant.
The 0.1.0 benchmark read quality from this table, which made its
headline numbers circular. Quality is now *measured* from response
text by ``scoring.score_response`` against golden answers.
"""
from __future__ import annotations

from dataclasses import dataclass

from cost_aware_router.classifier import Tier


@dataclass(frozen=True)
class ModelSpec:
    """A model in the routing table (price only — quality is measured)."""

    name: str
    tier: Tier
    price_per_1k_tokens: float


ROUTING_TABLE: dict[Tier, ModelSpec] = {
    Tier.CHEAP: ModelSpec("mock-mini", Tier.CHEAP, 0.0002),
    Tier.DEFAULT: ModelSpec("mock-standard", Tier.DEFAULT, 0.002),
    Tier.PREMIUM: ModelSpec("mock-frontier", Tier.PREMIUM, 0.012),
}

# Attempt order per routed tier: escalate upward on quality failure;
# the premium row degrades downward only after provider errors.
FALLBACK_CHAIN: dict[Tier, tuple[Tier, ...]] = {
    Tier.CHEAP: (Tier.CHEAP, Tier.DEFAULT, Tier.PREMIUM),
    Tier.DEFAULT: (Tier.DEFAULT, Tier.PREMIUM),
    Tier.PREMIUM: (Tier.PREMIUM, Tier.DEFAULT),
}


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token, min 1."""
    return max(1, len(text) // 4)
