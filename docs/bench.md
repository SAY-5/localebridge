# Bench

`apps/orchestrator/src/localebridge/bench.py` synthesizes a React app with N translatable strings spread across `files` files and measures three axes:

1. Extraction throughput: `strings/sec`, `files/sec`, AST-walk wall-clock, memory peak.
2. Translation throughput: `translations/sec` via the FakeTranslator across all 7 default target locales.
3. Validation throughput: `validations/sec` per axis (`icu`, `plural`, `unicode`, `length`).

## Commands

```bash
# One-off bench at N=10000
make bench

# Compare against committed baseline; fail if any throughput drops >30%
make bench-regress
```

## Baseline

`apps/orchestrator/bench_baseline.json` is the committed reference. CI runs the smoke test at N=500; the full N=10000 run is operator-triggered to avoid flakiness on shared runners. Refresh the baseline by deleting the file and re-running `bench-regress`.

## Reading the output

Throughput axes are higher-is-better. The regression gate flags any axis that drops by more than `--threshold` (default 0.30). Memory peak and extraction seconds are informational; intentional UI for triage, not gating.
