"""Classifier + cache tests."""
import time

from cost_aware_router.cache import ResponseCache, jaccard
from cost_aware_router.classifier import ComplexityClassifier, Tier


def test_simple_goes_cheap() -> None:
    assert ComplexityClassifier().classify("What is the capital of France?").tier == Tier.CHEAP


def test_complex_goes_premium() -> None:
    p = ("Prove and derive the theorem, optimise the algorithm architecture, debug the "
         "traceback step by step ``` def f(): pass ``` multi-step")
    assert ComplexityClassifier().classify(p).tier == Tier.PREMIUM


def test_medium_goes_default() -> None:
    p = "Write a product description for a coffee mug aimed at remote workers who love travel"
    assert ComplexityClassifier().classify(p).tier == Tier.DEFAULT


def test_score_bounds_edge_cases() -> None:
    c = ComplexityClassifier()
    assert 0.0 <= c.classify("").score <= 1.0
    assert 0.0 <= c.classify("x " * 500).score <= 1.0


def test_cache_exact_hit_and_miss() -> None:
    cache = ResponseCache(ttl_seconds=60)
    cache.put("hello world", "hi")
    assert cache.get("hello world") == "hi"
    assert cache.get("completely different zebra quantum") is None


def test_cache_ttl_expiry() -> None:
    cache = ResponseCache(ttl_seconds=0.05)
    cache.put("hello world", "hi")
    time.sleep(0.07)
    assert cache.get("hello world") is None


def test_semantic_lite_hit() -> None:
    cache = ResponseCache(ttl_seconds=60, semantic_threshold=0.8)
    cache.put("what is the capital of france", "Paris")
    assert cache.get("what is the capital of france today") == "Paris"


def test_jaccard_edge_cases() -> None:
    assert jaccard("a b", "a b") == 1.0
    assert jaccard("", "x") == 0.0
    assert jaccard("a", "b") == 0.0
