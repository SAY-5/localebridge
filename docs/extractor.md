# Extractor

The TypeScript extractor walks a React source tree and finds translatable strings via three patterns.

## Patterns

### 1. `t()` calls

Matches calls whose callee is `t` or ends in `.t`. The first argument must be a string literal; the optional second argument is an object literal whose `defaultValue` property supplies the source text.

```tsx
t("nav.home")
t("nav.home", { defaultValue: "Home" })
```

### 2. `<Trans>` component

JSX elements whose tag name is `Trans` with an `i18nKey` attribute. The children are flattened to a string and used as the default value. Self-closing variants read the `defaults` attribute.

```tsx
<Trans i18nKey="app.welcome">Welcome to LocaleBridge</Trans>
<Trans i18nKey="app.greeting" defaults="Hello, friend" />
```

### 3. JSDoc `@i18n` annotation

A JSX string-literal attribute preceded by a JSDoc block with `@i18n <key>` is captured. The key comes from the annotation; the default value comes from the attribute's string literal.

```tsx
<a /** @i18n nav.home */ aria-label="Home">x</a>
```

## Output

`extracted.json`: a flat array of `{key, default_value, source_file, line, context}`. Sorted by `source_file`, then `line`, then `key`, so the output is byte-stable across re-runs on the same input.

## CLI

```bash
node apps/extractor/dist/cli.js --src <path> --out <path>
```

## Implementation notes

ts-morph's `getLeadingCommentRanges()` returns nothing for trivia between JSX tokens. The JSDoc extractor reads raw source text between `attr.getFullStart()` and `attr.getStart()`, which is where the leading trivia actually lives.
