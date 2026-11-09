"""Router: classify -> cache -> provider, with a real quality gate.

Fallback semantics (documented, and tested):

- **Provider error**: retry the same tier once, then move along the
  fallback chain (upward; downward only from premium, as a last
  resort). Errored calls are not charged.
- **Quality failure**: the response is scored with
  ``scoring.score_response``. The call *is* charged (the provider did
  the work) and recorded, and if a higher tier remains the router
  escalates to it and discards the weak response. At the top tier the
  best available response is returned as-is.

Cache hits are free, tenant-scoped, and never counted as routed
calls in ``tracker.by_tier``.
"""
from __future__ import annotations

from dataclasses import dataclass

from cost_aware_router.cache import ResponseCache
from cost_aware_router.classifier import ComplexityClassifier, Tier
from cost_aware_router.config import Config
from cost_aware_router.errors import AllProvidersFailedError, ProviderError
from cost_aware_router.models import FALLBACK_CHAIN, ROUTING_TABLE, estimate_tokens
from cost_aware_router.providers import Provider, default_providers
from cost_aware_router.scoring import score_response
from cost_aware_router.tracker import CostTracker

_TIER_RANK = {Tier.CHEAP: 0, Tier.DEFAULT: 1, Tier.PREMIUM: 2}
DEFAULT_QUALITY_THRESHOLD = 0.5


@dataclass(frozen=True)
class RouteResult:
    """One routed response."""

    response: str
    tier: Tier
    model: str
    cached: bool
    classification_score: float
    quality: float | None = None
    attempts: int = 1


class ModelRouter:
    """Routes by complexity with caching, fallbacks and cost tracking."""

    def __init__(self, providers: dict[str, Provider] | None = None,
                 cache: ResponseCache | None = None, tracker: CostTracker | None = None,
                 config: Config | None = None,
                 expected_answers: dict[str, str] | None = None,
                 quality_threshold: float = DEFAULT_QUALITY_THRESHOLD) -> None:
        """Create a router (mock providers by default).

        ``expected_answers`` (prompt -> golden answer) switches the
        quality gate/scorer into golden mode and seeds the default
        providers' answer book; ``config.api_key`` is passed through
        to the providers.
        """
        cfg = config or Config.from_env()
        self._expected = expected_answers or {}
        self._providers = providers or default_providers(
            answer_book=self._expected or None, api_key=cfg.api_key)
        self.cache = cache or ResponseCache(cfg.cache_ttl_seconds, cfg.semantic_threshold)
        self.tracker = tracker or CostTracker()
        self._classifier = ComplexityClassifier()
        self._quality_threshold = quality_threshold

    def _score(self, prompt: str, response: str) -> float:
        return score_response(prompt, response, self._expected.get(prompt))

    def route(self, prompt: str, tenant: str = "default") -> RouteResult:
        """Route one prompt end to end for ``tenant``'s cache namespace."""
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        cls = self._classifier.classify(prompt)
        tokens = estimate_tokens(prompt) + 60
        cached = self.cache.get(prompt, tenant)
        if cached is not None:
            self.tracker.record(cls.tier, tokens, cached=True)
            return RouteResult(cached, cls.tier, "cache", True, cls.score, attempts=0)

        order = FALLBACK_CHAIN[cls.tier]
        attempts = 0
        last_error: ProviderError | None = None
        best: RouteResult | None = None
        for position, tier in enumerate(order):
            spec = ROUTING_TABLE[tier]
            provider = self._providers[spec.name]
            response: str | None = None
            for _try in range(2):  # one retry on provider error
                attempts += 1
                try:
                    response = provider.complete(prompt)
                    break
                except ProviderError as exc:
                    last_error = exc
            if response is None:
                continue  # tier down after retry: move along the chain
            quality = self._score(prompt, response)
            self.tracker.record(tier, tokens, quality=quality)  # charged even if gated
            candidate = RouteResult(response, tier, spec.name, False, cls.score,
                                    quality=quality, attempts=attempts)
            higher_remains = any(_TIER_RANK[t] > _TIER_RANK[tier] for t in order[position + 1:])
            if quality >= self._quality_threshold or not higher_remains:
                self.cache.put(prompt, response, tenant)
                return candidate
            best = candidate  # quality gate: escalate, keep as fallback
        if best is not None:
            return best
        raise AllProvidersFailedError(f"all providers failed for tier {cls.tier}: {last_error}")
