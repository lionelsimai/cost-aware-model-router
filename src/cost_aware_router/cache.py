"""Response cache: exact hash + TTL, semantic-lite via token overlap."""
from __future__ import annotations

import hashlib
import re
import time
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


class ResponseCache:
    """In-memory cache with TTL and semantic-lite lookup."""

    def __init__(self, ttl_seconds: float = 300.0, semantic_threshold: float = 0.85) -> None:
        """Create an empty cache."""
        self._ttl = ttl_seconds
        self._threshold = semantic_threshold
        self._entries: dict[str, _Entry] = {}
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _key(prompt: str) -> str:
        return hashlib.sha256(prompt.strip().lower().encode()).hexdigest()

    def get(self, prompt: str) -> str | None:
        """Return a cached response (exact, then semantic), or None."""
        now = time.monotonic()
        entry = self._entries.get(self._key(prompt))
        if entry is not None and entry.expires_at > now:
            self.hits += 1
            return entry.response
        for other in list(self._entries.values()):
            if other.expires_at > now and jaccard(prompt, other.prompt) >= self._threshold:
                self.hits += 1
                return other.response
        self.misses += 1
        return None

    def put(self, prompt: str, response: str) -> None:
        """Store a response."""
        self._entries[self._key(prompt)] = _Entry(prompt, response, time.monotonic() + self._ttl)

    def clear_expired(self) -> None:
        """Drop expired entries."""
        now = time.monotonic()
        self._entries = {k: v for k, v in self._entries.items() if v.expires_at > now}
