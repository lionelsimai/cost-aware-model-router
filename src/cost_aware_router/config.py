"""Environment configuration — keys from env only, never hardcoded."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Runtime config from ``ROUTER_*`` env vars."""

    cache_ttl_seconds: float = 300.0
    semantic_threshold: float = 0.85
    api_key: str = ""

    @classmethod
    def from_env(cls) -> Config:
        """Build from environment."""
        return cls(
            cache_ttl_seconds=float(os.environ.get("ROUTER_CACHE_TTL", "300")),
            semantic_threshold=float(os.environ.get("ROUTER_SEMANTIC_THRESHOLD", "0.85")),
            api_key=os.environ.get("ROUTER_API_KEY", ""),
        )
