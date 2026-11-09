# Cost-Aware Model Router

![CI](https://github.com/lionelsimai/cost-aware-model-router/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)

**Routes by complexity with caching and fallbacks — and measures quality instead of assuming it.**

Classifies prompts by complexity, routes cheap/default/premium, caches
repeats, escalates on quality failure, and tracks spend against an
all-premium baseline. Zero dependencies — swap `MockProvider` for a
real client behind the `Provider` protocol.

## What 0.1.1 fixed (adversarial audit)

The 0.1.0 headline ("94.2% saving, 1.1% quality drop") was **circular**:
quality was read from constants in the routing table, the traffic was
76% cache repeats, and the "quality gate" never compared anything.
0.1.1 deletes those numbers everywhere and rebuilds the measurement:

- **Quality is measured.** `scoring.score_response` scores real response
  text against golden expected answers (keyword recall), or a coverage/
  length heuristic when no golden answer exists. The per-tier quality
  constants in `models.py` are gone.
- **Headline benchmark = unique prompts only.** 18 natural golden cases,
  no repeats. Cache savings are a separate, labelled scenario.
- **The quality gate is real.** A response below the threshold is
  charged, recorded, and the request escalates UP a tier. Provider
  errors retry once, then follow the fallback chain.
- **Cache is bounded and tenant-scoped.** LRU with `max_entries`
  (default 1024); keys are namespaced per tenant; `by_tier` counts
  provider calls only, never cache hits.

## Measured benchmark (0.1.1, real output)

```
$ python -m cost_aware_router benchmark
cases=18 unique prompts, no repeats
by_tier={'cheap': 9, 'default': 6, 'premium': 3} spend=$0.0050 baseline_premium=$0.0178 saving=71.7%
measured quality: routed=0.982 premium=1.0 quality_drop=1.8% (golden-answer keyword recall)
cache scenario (same traffic twice): requests=36 cache_hits=18 spend=$0.0050 vs $0.0050 for the unique pass
```

Honest reading: **71.7% saving, 1.8% measured quality drop** on this
mock traffic mix — and the entire drop comes from one case: a short
prompt ("Why does quicksort degrade to O(n^2)…") that the heuristic
classifier routes to the cheap tier, whose simulated answer truncates
the third sentence (scored 0.667 vs 1.0). That misroute is in the
benchmark on purpose: it is the known weakness of keyword routing,
shown rather than hidden. The mock providers simulate tier quality by
completeness (declared simulation parameters, not measurements); plug
in real providers and the scorer measures their real output the same
way.

## Quickstart

```bash
pip install -e .
python -m cost_aware_router route "What is the capital of France?"
# tier=cheap model=mock-mini cached=False score=0.05
# [mock-mini] answer to: What is the capital of France?

python -m cost_aware_router benchmark
python examples/example_routing.py
```

## Example output (real)

```
$ python examples/example_routing.py
cheap    mock-mini      score=0.05 :: What is the capital of France?
default  mock-standard  score=0.35 :: Write a product description for a coffee mug aimed
premium  mock-frontier  score=1.0 :: Prove the algorithm is optimal, derive its complex
spend=$0.0012 baseline=$0.0028 saving=58.0%
```

## Fallback semantics

| Failure | Behaviour |
|---|---|
| Provider error | Retry same tier once → next tier in chain (premium degrades to default last). Errored calls are not charged. |
| Quality below threshold | Call is charged + recorded; escalate to a higher tier if one remains, else return best effort. |
| Cache hit | Free, tenant-scoped, not counted in `by_tier`. |

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `ROUTER_TTL_SECONDS` | `300` | Cache TTL |
| `ROUTER_SEMANTIC_THRESHOLD` | `0.85` | Semantic cache-match threshold |
| `ROUTER_API_KEY` | _(empty)_ | Passed through to providers (`Config.api_key`) |

## Development

```bash
pip install -e .[dev]
python -m pytest        # 24 passed
ruff check src tests benchmarks examples
```

## License

MIT — see `LICENSE`.
