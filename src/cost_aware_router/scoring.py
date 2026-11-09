"""Response quality scoring — measured from text, never from constants.

Two modes:

- **Golden mode** (benchmarks): score = recall of the golden answer's
  content words in the response. Exact, reproducible, and tied to a
  published expected answer per prompt.
- **Heuristic mode** (live routing / quality gate): score = a sanity
  blend of prompt-content coverage and response length, with empty or
  refusal-style responses scoring 0. It exists so the quality gate has
  something real to compare — it is *not* a claim about answer truth.
"""
from __future__ import annotations

import re

_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "by", "at", "as", "it", "its", "this",
    "that", "from", "into", "how", "what", "why", "when", "which", "who",
})
_REFUSALS = ("i don't know", "i do not know", "i cannot answer", "i can't answer",
             "no idea", "unable to answer", "as an ai")


def content_words(text: str) -> set[str]:
    """Lowercased content words (len > 2, stopwords removed)."""
    return {w for w in re.findall(r"[a-z0-9']+", text.lower())
            if len(w) > 2 and w not in _STOPWORDS}


def score_response(prompt: str, response: str, expected: str | None = None) -> float:
    """Score a response 0.0-1.0 (see module docstring for the modes)."""
    if not response.strip():
        return 0.0
    if expected is not None:
        keywords = content_words(expected)
        if not keywords:
            return 1.0
        hits = keywords & content_words(response)
        return round(len(hits) / len(keywords), 3)
    low = response.lower()
    if any(refusal in low for refusal in _REFUSALS):
        return 0.0
    prompt_words = content_words(prompt)
    # No content words in the prompt (e.g. "What is 2 + 2?") makes
    # coverage undefined — treat it as neutral, not as zero.
    coverage = (len(prompt_words & content_words(response)) / len(prompt_words)
                if prompt_words else 1.0)
    length_score = min(1.0, len(response.split()) / 10)
    return round(0.5 * coverage + 0.5 * length_score, 3)
