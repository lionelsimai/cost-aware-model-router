"""Routing table: tiers, mock models, prices ($ per 1k tokens)."""
from __future__ import annotations

from dataclasses import dataclass

from cost_aware_router.classifier import Tier


@dataclass(frozen=True)
class ModelSpec:
    """A model in the routing table."""

    name: str
    tier: Tier
    price_per_1k_tokens: float
    quality: float  # 0-1, measured on the internal golden set (mock)


ROUTING_TABLE: dict[Tier, ModelSpec] = {
    Tier.CHEAP: ModelSpec("mock-mini", Tier.CHEAP, 0.0002, 0.955),
    Tier.DEFAULT: ModelSpec("mock-standard", Tier.DEFAULT, 0.002, 0.965),
    Tier.PREMIUM: ModelSpec("mock-frontier", Tier.PREMIUM, 0.012, 0.97),
}

# Fallback chain: try the routed tier, then step up.
FALLBACK_CHAIN: dict[Tier, tuple[Tier, ...]] = {
    Tier.CHEAP: (Tier.CHEAP, Tier.DEFAULT, Tier.PREMIUM),
    Tier.DEFAULT: (Tier.DEFAULT, Tier.PREMIUM),
    Tier.PREMIUM: (Tier.PREMIUM, Tier.DEFAULT),
}


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token, min 1."""
    return max(1, len(text) // 4)
