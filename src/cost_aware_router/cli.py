"""CLI: route one prompt, or run the benchmark."""
from __future__ import annotations

import argparse
import sys

from cost_aware_router.benchmark_data import TRAFFIC
from cost_aware_router.errors import RouterError
from cost_aware_router.router import ModelRouter


def run_benchmark(router: ModelRouter | None = None) -> ModelRouter:
    """Route the simulated traffic mix (plus repeats, to exercise the cache)."""
    router = router or ModelRouter()
    for prompt in TRAFFIC:
        router.route(prompt)
    for prompt in TRAFFIC[:10]:  # repeats -> cache hits
        router.route(prompt)
    return router


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(prog="model-router", description="Cost-aware model routing.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    route_p = sub.add_parser("route", help="Route a single prompt")
    route_p.add_argument("prompt")
    sub.add_parser("benchmark", help="Simulated traffic vs single-model baseline")
    args = parser.parse_args(argv)
    try:
        router = ModelRouter()
        if args.cmd == "route":
            r = router.route(args.prompt)
            print(f"tier={r.tier} model={r.model} cached={r.cached} score={r.classification_score}")
            print(r.response)
            return 0
        run_benchmark(router)
        t = router.tracker
        print(f"requests={t.requests} by_tier={t.by_tier} cache_hits={t.cache_hits}")
        print(f"spend=${t.spend_usd:.4f} baseline_premium=${t.baseline_usd:.4f} saving={t.saving_pct}%")
        print(f"avg_quality={t.avg_quality} (premium=0.97, quality drop="
              f"{round(100 * (0.97 - t.avg_quality) / 0.97, 1)}%)")
        return 0
    except (RouterError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
