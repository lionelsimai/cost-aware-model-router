"""Router: classify -> cache -> provider with fallback + quality gate."""
from __future__ import annotations

from dataclasses import dataclass

from cost_aware_router.cache import ResponseCache
from cost_aware_router.classifier import ComplexityClassifier, Tier
from cost_aware_router.config import Config
from cost_aware_router.errors import AllProvidersFailedError, ProviderError
from cost_aware_router.models import FALLBACK_CHAIN, ROUTING_TABLE, estimate_tokens
from cost_aware_router.providers import MockProvider, default_providers
from cost_aware_router.tracker import CostTracker

QUALITY_GATE = {Tier.CHEAP: 0.80, Tier.DEFAULT: 0.88, Tier.PREMIUM: 0.90}


@dataclass(frozen=True)
class RouteResult:
    """One routed response."""

    response: str
    tier: Tier
    model: str
    cached: bool
    classification_score: float


class ModelRouter:
    """Routes by complexity with caching, fallbacks and cost tracking."""

    def __init__(self, providers: dict[str, MockProvider] | None = None,
                 cache: ResponseCache | None = None, tracker: CostTracker | None = None,
                 config: Config | None = None) -> None:
        """Create a router (mock providers by default)."""
        cfg = config or Config.from_env()
        self._providers = providers or default_providers()
        self.cache = cache or ResponseCache(cfg.cache_ttl_seconds, cfg.semantic_threshold)
        self.tracker = tracker or CostTracker()
        self._classifier = ComplexityClassifier()

    def route(self, prompt: str) -> RouteResult:
        """Route one prompt end to end."""
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        cls = self._classifier.classify(prompt)
        cached = self.cache.get(prompt)
        tokens = estimate_tokens(prompt) + 60
        if cached is not None:
            self.tracker.record(cls.tier, tokens, cached=True)
            return RouteResult(cached, cls.tier, "cache", True, cls.score)
        last_error: ProviderError | None = None
        for tier in FALLBACK_CHAIN[cls.tier]:
            spec = ROUTING_TABLE[tier]
            provider = self._providers[spec.name]
            try:
                response = provider.complete(prompt)
            except ProviderError as exc:
                last_error = exc
                continue
            if spec.quality < QUALITY_GATE[cls.tier] and tier != Tier.PREMIUM:
                continue  # quality gate: step up
            self.cache.put(prompt, response)
            self.tracker.record(tier, tokens)
            return RouteResult(response, tier, spec.name, False, cls.score)
        raise AllProvidersFailedError(f"all providers failed for tier {cls.tier}: {last_error}")
