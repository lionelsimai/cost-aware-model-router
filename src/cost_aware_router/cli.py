"""CLI: route one prompt, or run the measured benchmark."""
from __future__ import annotations

import argparse
import sys

from cost_aware_router.bench import run_benchmark as _run_full_benchmark
from cost_aware_router.benchmark_data import TRAFFIC
from cost_aware_router.errors import RouterError
from cost_aware_router.router import ModelRouter


def run_benchmark(router: ModelRouter | None = None) -> ModelRouter:
    """Route the unique golden traffic once (no repeats) and return the router."""
    router = router or ModelRouter()
    for prompt in TRAFFIC:
        router.route(prompt)
    return router


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(prog="model-router", description="Cost-aware model routing.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    route_p = sub.add_parser("route", help="Route a single prompt")
    route_p.add_argument("prompt")
    sub.add_parser("benchmark", help="Measured benchmark on unique golden cases")
    args = parser.parse_args(argv)
    try:
        router = ModelRouter()
        if args.cmd == "route":
            r = router.route(args.prompt)
            print(f"tier={r.tier} model={r.model} cached={r.cached} score={r.classification_score}")
            print(r.response)
            return 0
        report = _run_full_benchmark()
        print(f"cases={report.cases} unique prompts, no repeats")
        print(f"by_tier={report.by_tier} spend=${report.routed_spend_usd:.4f} "
              f"baseline_premium=${report.baseline_spend_usd:.4f} saving={report.saving_pct}%")
        print(f"measured quality: routed={report.routed_quality} premium={report.premium_quality} "
              f"quality_drop={report.quality_drop_pct}% (golden-answer keyword recall)")
        print(f"cache scenario (same traffic twice): requests={report.cache_requests} "
              f"cache_hits={report.cache_hits} spend=${report.cache_spend_usd:.4f} "
              f"vs ${report.unique_spend_usd:.4f} for the unique pass")
        return 0
    except (RouterError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
