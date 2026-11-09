# Changelog

## [0.1.1] - 2026-11-09
### Fixed (adversarial-audit remediation)
- Removed the circular 94.2% saving / 1.1% quality-drop headline from
  README, benchmark, docstrings and package metadata: quality was read
  from routing-table constants and the traffic was mostly cache hits.
- Quality is now measured: `scoring.score_response` scores response text
  against golden answers (keyword recall) or a coverage/length
  heuristic; per-tier `quality` constants deleted from `models.py`.
- Benchmark rebuilt on 18 unique natural golden cases (no repeats);
  measured result: 71.7% saving, quality 0.982 routed vs 1.0 premium
  (1.8% drop, entirely from one known under-routed case). Cache benefit
  is a separate labelled scenario.
- Quality gate is real: below-threshold responses are charged, recorded
  and escalated to a higher tier; provider errors retry once then follow
  the chain (semantics documented). One 0.1.0 test that asserted the
  constant-derived headline was replaced by a measured-metrics test.
- Cache: bounded LRU (`max_entries`, default 1024) + tenant-namespaced
  keys; `by_tier` no longer counts cache hits as routed calls.
### Added
- `Provider` protocol (runtime-checkable) implemented by `MockProvider`;
  `Config.api_key` (`ROUTER_API_KEY`) now wired through to providers.
- Tests for gate escalation + charging, tenant isolation, LRU bound,
  `by_tier` cache exclusion and protocol compliance.

## [0.1.0] - 2026-11-09
### Added
- Complexity classifier, 3-tier routing table, cache (exact + semantic-lite)
- Fallback chain, cost tracker, benchmark showing >50% saving vs premium baseline
