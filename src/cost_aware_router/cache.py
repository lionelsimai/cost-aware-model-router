"""Response cache: exact hash + TTL, semantic-lite, bounded LRU, per-tenant.

Keys include a tenant namespace — one tenant's cached response is
never served to another. Eviction is LRU past ``max_entries``.
"""
from __future__ import annotations

import hashlib
import re
import time
from collections import OrderedDict
from dataclasses import dataclass


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def jaccard(a: str, b: str) -> float:
    """Token-overlap (Jaccard) similarity."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


@dataclass
class _Entry:
    prompt: str
    response: str
    expires_at: float
    tenant: str = "default"


class ResponseCache:
    """In-memory LRU cache with TTL, tenant namespaces and semantic-lite lookup."""

    def __init__(self, ttl_seconds: float = 300.0, semantic_threshold: float = 0.85,
                 max_entries: int = 1024) -> None:
        """Create an empty cache bounded to ``max_entries`` (LRU eviction)."""
        self._ttl = ttl_seconds
        self._threshold = semantic_threshold
        self._max_entries = max(1, max_entries)
        self._entries: OrderedDict[str, _Entry] = OrderedDict()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _key(prompt: str, tenant: str) -> str:
        raw = f"{tenant}\x00{prompt.strip().lower()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._entries)

    def get(self, prompt: str, tenant: str = "default") -> str | None:
        """Return a cached response *for this tenant*, or None."""
        now = time.monotonic()
        key = self._key(prompt, tenant)
        entry = self._entries.get(key)
        if entry is not None and entry.expires_at > now:
            self._entries.move_to_end(key)
            self.hits += 1
            return entry.response
        for other_key, other in list(self._entries.items()):
            if other.tenant != tenant:
                continue
            if other.expires_at > now and jaccard(prompt, other.prompt) >= self._threshold:
                self._entries.move_to_end(other_key)
                self.hits += 1
                return other.response
        self.misses += 1
        return None

    def put(self, prompt: str, response: str, tenant: str = "default") -> None:
        """Store a response under the tenant's namespace (LRU-bounded)."""
        key = self._key(prompt, tenant)
        self._entries[key] = _Entry(prompt, response, time.monotonic() + self._ttl, tenant)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def clear_expired(self) -> None:
        """Drop expired entries."""
        now = time.monotonic()
        self._entries = OrderedDict(
            (k, v) for k, v in self._entries.items() if v.expires_at > now)
