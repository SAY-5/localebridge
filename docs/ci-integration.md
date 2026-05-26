# CI Integration

LocaleBridge runs on every PR via a composite GitHub Action.

## Composite action

`.github/actions/localebridge-action/action.yml` exposes three inputs:

- `src`: source directory to walk
- `locales-dir`: directory to write `<lang>.json` files into
- `targets`: comma-separated locale codes (default: `es,fr,de,ja,ar,zh-CN,hi`)

## Wiring it into another repo

```yaml
- uses: SAY-5/localebridge/.github/actions/localebridge-action@main
  with:
    src: apps/web/src
    locales-dir: apps/web/locales
    targets: es,fr,de,ja
```

The action builds the extractor, runs the orchestrator pipeline, and writes a job-summary block with the per-locale key counts.

## Hermetic CI

CI never calls a real LLM. The orchestrator uses `FakeTranslator` by default. The `ClaudeProvider` stub raises unless `LOCALEBRIDGE_LIVE_LLM=1` is explicitly set, which only happens for opt-in production deployments.

## Job matrix

The base CI has six jobs:

1. `extractor` — typecheck + build + vitest
2. `orchestrator` (matrix: py3.11, py3.12) — ruff + mypy strict + pytest
3. `integration` — extractor build, orchestrator run against `examples/react-app`
4. `docker` — build the orchestrator image, import-check `localebridge`
5. `action-self-test` — run the composite action against the example app
