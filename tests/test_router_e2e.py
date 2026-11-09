"""Router, fallback, tracker + end-to-end benchmark tests."""
import pytest

from cost_aware_router.classifier import Tier
from cost_aware_router.cli import main, run_benchmark
from cost_aware_router.errors import AllProvidersFailedError
from cost_aware_router.models import ROUTING_TABLE
from cost_aware_router.providers import MockProvider
from cost_aware_router.router import ModelRouter


def test_route_simple_uses_cheap() -> None:
    r = ModelRouter().route("What is 2 + 2?")
    assert r.tier == Tier.CHEAP and not r.cached


def test_second_identical_route_is_cached() -> None:
    router = ModelRouter()
    router.route("What is 2 + 2?")
    assert router.route("What is 2 + 2?").cached


def test_empty_prompt_rejected() -> None:
    with pytest.raises(ValueError):
        ModelRouter().route("   ")


def test_fallback_on_provider_error() -> None:
    providers = {spec.name: MockProvider(spec) for spec in ROUTING_TABLE.values()}
    providers["mock-mini"] = MockProvider(ROUTING_TABLE[Tier.CHEAP], fail_times=5)
    r = ModelRouter(providers=providers).route("What is 2 + 2?")
    assert r.model == "mock-standard"  # stepped up the fallback chain


def test_all_providers_fail_raises() -> None:
    providers = {s.name: MockProvider(s, fail_times=99) for s in ROUTING_TABLE.values()}
    with pytest.raises(AllProvidersFailedError):
        ModelRouter(providers=providers).route("What is 2 + 2?")


def test_benchmark_meets_headline_target() -> None:
    router = run_benchmark(ModelRouter())
    t = router.tracker
    assert t.saving_pct >= 50.0
    drop = 100 * (0.97 - t.avg_quality) / 0.97
    assert drop < 2.0


def test_e2e_cli(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["route", "What is the capital of France?"]) == 0
    assert "tier=cheap" in capsys.readouterr().out
    assert main(["benchmark"]) == 0
    assert "saving=" in capsys.readouterr().out
