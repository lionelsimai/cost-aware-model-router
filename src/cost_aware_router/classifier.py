"""Heuristic complexity classifier."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class Tier(StrEnum):
    """Model tier."""

    CHEAP = "cheap"
    DEFAULT = "default"
    PREMIUM = "premium"


_COMPLEX = ("prove", "derive", "optimise", "optimize", "architecture", "debug", "refactor",
            "algorithm", "theorem", "multi-step", "analyse deeply", "analyze deeply")
_CODE = ("def ", "class ", "```", "function", "stack trace", "traceback")
_SIMPLE = ("what is", "define", "translate", "summarise in one", "summarize in one", "list")


@dataclass(frozen=True)
class Classification:
    """Classifier output."""

    score: float
    tier: Tier
    reasons: tuple[str, ...]


class ComplexityClassifier:
    """Score prompt complexity 0.0-1.0 from transparent heuristics."""

    def classify(self, prompt: str) -> Classification:
        """Classify a prompt into a tier."""
        low = prompt.lower()
        words = len(re.findall(r"\w+", low))
        score = 0.15
        reasons: list[str] = [f"base words={words}"]
        if words > 120:
            score += 0.35
            reasons.append("long prompt")
        elif words > 40:
            score += 0.25
            reasons.append("medium-long prompt")
        elif words >= 15:
            score += 0.20
            reasons.append("medium prompt")
        hits = sum(1 for k in _COMPLEX if k in low)
        if hits:
            score += min(0.45, 0.18 * hits)
            reasons.append(f"complex keywords x{hits}")
        if any(k in low for k in _CODE):
            score += 0.25
            reasons.append("code content")
        if low.count("?") >= 3 or "step by step" in low:
            score += 0.15
            reasons.append("multi-part reasoning")
        if any(k in low for k in _SIMPLE) and words < 25 and hits == 0:
            score -= 0.10
            reasons.append("simple lookup")
        score = max(0.0, min(1.0, score))
        tier = Tier.CHEAP if score < 0.35 else Tier.DEFAULT if score < 0.65 else Tier.PREMIUM
        return Classification(score=round(score, 3), tier=tier, reasons=tuple(reasons))
