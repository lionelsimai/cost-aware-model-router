"""Example: route three prompts of rising complexity."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cost_aware_router.router import ModelRouter

PROMPTS = [
    "What is the capital of France?",
    "Write a product description for a coffee mug aimed at remote workers who love travel",
    "Prove the algorithm is optimal, derive its complexity, debug this traceback step by step",
]


def main() -> int:
    """Run the example."""
    router = ModelRouter()
    for prompt in PROMPTS:
        r = router.route(prompt)
        print(f"{r.tier:8} {r.model:14} score={r.classification_score} :: {prompt[:50]}")
    t = router.tracker
    print(f"spend=${t.spend_usd:.4f} baseline=${t.baseline_usd:.4f} saving={t.saving_pct}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
