"""Quality gate, cache bounds/tenancy, provider protocol, config wiring."""
import pytest

from cost_aware_router.cache import ResponseCache
from cost_aware_router.classifier import Tier
from cost_aware_router.config import Config
from cost_aware_router.models import ROUTING_TABLE
from cost_aware_router.providers import MockProvider, Provider, default_providers
from cost_aware_router.router import ModelRouter
from cost_aware_router.scoring import score_response


class _RefusingProvider(MockProvider):
    """A provider whose answers are pure refusal (quality 0)."""

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return "I don't know."


def test_quality_gate_escalates_up_and_charges_failed_call() -> None:
    providers = default_providers()
    providers["mock-mini"] = _RefusingProvider(ROUTING_TABLE[Tier.CHEAP])
    router = ModelRouter(providers=providers)
    result = router.route("What is the capital of France?")
    assert result.model == "mock-standard"  # escalated UP a tier
    assert result.quality is not None and result.quality > 0
    t = router.tracker
    assert t.by_tier == {"cheap": 1, "default": 1}  # the gated call was recorded
    cheap_cost = ROUTING_TABLE[Tier.CHEAP].price_per_1k_tokens
    assert t.spend_usd > cheap_cost * 80 / 1000  # ... and charged, not free


def test_quality_gate_can_fire_on_scorer() -> None:
    assert score_response("anything", "I don't know.") == 0.0
    assert score_response("q", "", None) == 0.0
    assert score_response("What is the capital of France?",
                          "Paris is the capital of France.",
                          "Paris is the capital of France.") == 1.0


def test_cache_tenant_isolation() -> None:
    cache = ResponseCache(ttl_seconds=60)
    cache.put("hello world", "hi alice", tenant="alice")
    assert cache.get("hello world", tenant="alice") == "hi alice"
    assert cache.get("hello world", tenant="bob") is None  # never cross-tenant
    assert cache.get("hello world today", tenant="bob") is None  # semantic too


def test_cache_lru_bound() -> None:
    cache = ResponseCache(ttl_seconds=60, max_entries=3)
    for i in range(5):
        cache.put(f"prompt number {i} zebra", f"r{i}")
    assert cache.size == 3
    assert cache.get("prompt number 0 zebra") is None  # evicted (LRU)
    assert cache.get("prompt number 4 zebra") == "r4"


def test_by_tier_excludes_cache_hits() -> None:
    router = ModelRouter()
    router.route("What is the capital of France?")
    router.route("What is the capital of France?")
    t = router.tracker
    assert t.cache_hits == 1
    assert sum(t.by_tier.values()) == 1  # one provider call, not two


def test_router_tenant_namespaces_cache() -> None:
    router = ModelRouter()
    router.route("What is the capital of France?", tenant="alice")
    assert not router.route("What is the capital of France?", tenant="bob").cached
    assert router.route("What is the capital of France?", tenant="alice").cached


def test_provider_protocol_and_mock_compliance() -> None:
    provider = MockProvider(ROUTING_TABLE[Tier.CHEAP])
    assert isinstance(provider, Provider)
    assert provider.complete("hello there friend").startswith("[mock-mini]")


def test_api_key_wired_from_config_to_providers() -> None:
    providers = default_providers(api_key="sk-test-123")
    assert all(p.api_key == "sk-test-123" for p in providers.values())
    router = ModelRouter(config=Config(api_key="sk-test-123"))
    assert router.route("What is the capital of France?").model == "mock-mini"


def test_empty_prompt_still_rejected() -> None:
    with pytest.raises(ValueError):
        ModelRouter().route("   ")
