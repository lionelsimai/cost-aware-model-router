"""Simulated traffic mix for benchmarks (deterministic, no randomness)."""
from __future__ import annotations

SIMPLE = [
    "What is the capital of France?", "Define photosynthesis", "Translate hello to Spanish",
    "What is 12 + 7?", "List three colours", "What is a noun?", "Define gravity simply",
    "Translate thank you to French", "What is the boiling point of water?", "List two planets",
] * 4
MEDIUM = [
    "Summarise the pros and cons of remote work for a 20-person startup team in a short memo",
    "Write a product description for a coffee mug aimed at remote workers who love travel",
    "Explain how caching works in web apps with an example for a junior developer audience",
    "Draft an email to a customer apologising for a delayed shipment and offering a discount",
] * 3
COMPLEX = [
    ("Prove the algorithm is optimal, derive its time complexity, debug this traceback and "
     "refactor the architecture step by step: ``` def f(x): return x ``` multi-step analysis"),
    ("Derive a theorem proof, optimise the algorithm architecture, and analyse deeply the "
     "multi-step trade-offs in this stack trace with a full refactor plan and proof sketch"),
] * 2

TRAFFIC: list[str] = SIMPLE + MEDIUM + COMPLEX
