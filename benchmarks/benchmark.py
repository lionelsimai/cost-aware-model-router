"""Benchmark: simulated traffic spend vs single-model (all-premium) baseline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cost_aware_router.cli import run_benchmark
from cost_aware_router.router import ModelRouter


def main() -> int:
    """Run the benchmark and assert the headline targets."""
    router = run_benchmark(ModelRouter())
    t = router.tracker
    drop = round(100 * (0.97 - t.avg_quality) / 0.97, 1)
    print(f"requests={t.requests} by_tier={t.by_tier} cache_hits={t.cache_hits}")
    print(f"spend=${t.spend_usd:.4f} baseline_premium=${t.baseline_usd:.4f} saving={t.saving_pct}%")
    print(f"avg_quality={t.avg_quality} quality_drop={drop}%")
    ok = t.saving_pct >= 50.0 and drop < 2.0
    print(f"target: >=50% saving and <2% quality drop -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
