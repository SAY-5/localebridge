# LocaleBridge

Continuous-localization pipeline for web applications. A TypeScript extractor walks a React source tree to find translatable strings, a Python orchestrator routes them through translation and review, validators check ICU MessageFormat correctness, Unicode safety, and plural-rule coverage, and the result is written back to per-locale JSON files. Designed to run in CI on every PR.

## What it does

1. Walk a React/TypeScript codebase and extract translatable strings from three patterns:
   - `t("translation.key")` calls from `useTranslation()` / `i18next`
   - Literal text wrapped in `<Trans>...</Trans>`
   - Props marked with a JSDoc `@i18n` annotation
2. Route each extracted key through a translator (FakeTranslator for tests, Claude-shaped provider for production).
3. Validate every target locale for:
   - ICU MessageFormat parse correctness
   - Unicode normalization (NFC) and absence of bidi-control / zero-width attacks
   - Plural-category coverage per CLDR rules for that locale
   - Length budget against the source (overflow warning)
4. Write the approved translations back to `locales/<lang>.json` files.
5. Run the whole pipeline as a GitHub Action that posts a diff comment on the PR.

## Stack

- Extractor: TypeScript 5, ts-morph, commander, Node 20
- Orchestrator: Python 3.12, FastAPI, SQLAlchemy, Pydantic, Postgres
- Validators: `@formatjs/icu-messageformat-parser`, Python `icu`-compatible plural rules
- CI: GitHub Actions composite action
- Local: Docker Compose for the orchestrator + Postgres

## Locale targets (default suite)

en (source), es, fr, de, ja, ar (RTL), zh-CN, hi (multi-plural-category).

## Layout

```
apps/
  extractor/         TypeScript CLI (AST walker, three extractor strategies)
  orchestrator/      Python FastAPI service (translation memory, validators, writer)
examples/
  react-app/         tiny sample React app, ~30 translatable keys
.github/
  workflows/         CI: lint, typecheck, test (TS and Py), integration, docker, action-self-test
  actions/           composite action wrapper
docs/                extractor, validators, workflow, ci-integration, icu-messageformat
```

## Quickstart

```bash
pnpm install
poetry -C apps/orchestrator install
make e2e
```

The end-to-end run extracts strings from `examples/react-app`, routes them through the FakeTranslator, validates each locale, and writes back to `examples/react-app/locales/<lang>.json`.

## How this fits

LocaleBridge is the localization layer that sits behind React frontends. Adjacent work in this portfolio:

- `SAY-5/subscription-portal` and `SAY-5/recommendation-quiz` are React frontends that consume translated strings. LocaleBridge produces the locale files those apps load at runtime.
- `SAY-5/live-events-spa` is an i18n-friendly SPA; LocaleBridge is the upstream pipeline that keeps its translations synchronized with source changes.

## License

MIT.
