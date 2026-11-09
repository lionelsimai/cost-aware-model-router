"""Benchmark: measured spend + quality on unique golden cases.

Quality is scored from response text against the golden answers —
there is no target assertion here beyond the mechanical one (routed
spend must beat the all-premium baseline on this mix). The numbers
printed are whatever the measurement produces; see the README for
the current measured values and what drives them.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cost_aware_router.bench import run_benchmark


def main() -> int:
    """Run the measured benchmark."""
    r = run_benchmark()
    print(f"cases={r.cases} unique prompts, no repeats")
    print(f"by_tier={r.by_tier} spend=${r.routed_spend_usd:.4f} "
          f"baseline_premium=${r.baseline_spend_usd:.4f} saving={r.saving_pct}%")
    print(f"measured quality: routed={r.routed_quality} premium={r.premium_quality} "
          f"quality_drop={r.quality_drop_pct}% (golden-answer keyword recall)")
    print(f"cache scenario (same traffic twice): requests={r.cache_requests} "
          f"cache_hits={r.cache_hits} spend=${r.cache_spend_usd:.4f} "
          f"vs ${r.unique_spend_usd:.4f} unique pass")
    ok = r.routed_spend_usd < r.baseline_spend_usd
    print(f"mechanics check: routed spend < all-premium baseline -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
