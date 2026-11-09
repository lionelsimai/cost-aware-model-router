"""Mock providers — offline, deterministic, no API keys or GPU."""
from __future__ import annotations

from cost_aware_router.errors import ProviderError
from cost_aware_router.models import ROUTING_TABLE, ModelSpec


class MockProvider:
    """Simulates a model: quality from the spec, optional injected failures."""

    def __init__(self, spec: ModelSpec, fail_times: int = 0) -> None:
        """Create a provider; ``fail_times`` forces the next N calls to fail."""
        self.spec = spec
        self._fail_times = fail_times
        self.calls = 0

    def complete(self, prompt: str) -> str:
        """Return a deterministic mock completion."""
        self.calls += 1
        if self._fail_times > 0:
            self._fail_times -= 1
            raise ProviderError(f"{self.spec.name} unavailable (simulated)")
        return f"[{self.spec.name}] answer to: {prompt[:80]}"


def default_providers() -> dict[str, MockProvider]:
    """One mock provider per tier."""
    return {spec.name: MockProvider(spec) for spec in ROUTING_TABLE.values()}
