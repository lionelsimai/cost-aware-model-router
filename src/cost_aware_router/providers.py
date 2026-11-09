"""Providers: a ``Provider`` protocol plus deterministic mock providers.

A mock provider's *behaviour* is simulated, transparently: when a
prompt is in its answer book it returns the golden answer truncated
to a tier-dependent fraction of its sentences (cheap models give
shorter, less complete answers — that is the simulation), so the
benchmark's quality scorer measures real differences in response
text. The completeness fractions are simulation parameters, declared
here — they are never reported as measurements.
"""
from __future__ import annotations

import math
import re
from typing import Protocol, runtime_checkable

from cost_aware_router.classifier import Tier
from cost_aware_router.errors import ProviderError
from cost_aware_router.models import ROUTING_TABLE, ModelSpec

# Simulation parameter: fraction of a golden answer's sentences a tier
# typically returns. Premium is untruncated by definition of the sim.
COMPLETENESS: dict[Tier, float] = {Tier.CHEAP: 0.6, Tier.DEFAULT: 0.85, Tier.PREMIUM: 1.0}


@runtime_checkable
class Provider(Protocol):
    """Anything that can complete a prompt for a priced tier."""

    spec: ModelSpec

    def complete(self, prompt: str) -> str:
        """Return a completion for ``prompt`` (or raise ProviderError)."""
        ...


def _truncate_sentences(text: str, fraction: float) -> str:
    if fraction >= 1.0:
        return text
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    if len(sentences) <= 1:
        return text
    keep = max(1, math.ceil(len(sentences) * fraction))
    return " ".join(sentences[:keep])


class MockProvider:
    """Simulates a model: deterministic, offline, optional failures."""

    def __init__(self, spec: ModelSpec, fail_times: int = 0,
                 answer_book: dict[str, str] | None = None,
                 completeness: float | None = None,
                 api_key: str | None = None) -> None:
        """Create a provider; ``fail_times`` forces the next N calls to fail.

        ``api_key`` is accepted (and would authenticate a real adapter);
        the mock never uses it and never logs it.
        """
        self.spec = spec
        self._fail_times = fail_times
        self._answer_book = answer_book or {}
        self._completeness = COMPLETENESS[spec.tier] if completeness is None else completeness
        self.api_key = api_key
        self.calls = 0

    def complete(self, prompt: str) -> str:
        """Return a deterministic mock completion."""
        self.calls += 1
        if self._fail_times > 0:
            self._fail_times -= 1
            raise ProviderError(f"{self.spec.name} unavailable (simulated)")
        if prompt in self._answer_book:
            return _truncate_sentences(self._answer_book[prompt], self._completeness)
        return f"[{self.spec.name}] answer to: {prompt[:80]}"


def default_providers(answer_book: dict[str, str] | None = None,
                      api_key: str | None = None) -> dict[str, Provider]:
    """One mock provider per tier, sharing an optional answer book."""
    return {spec.name: MockProvider(spec, answer_book=answer_book, api_key=api_key)
            for spec in ROUTING_TABLE.values()}
