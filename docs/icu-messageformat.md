# ICU MessageFormat

LocaleBridge treats every translatable string as an ICU MessageFormat message.
The validator (`localebridge.validators.icu`) parses structure and the plural
validator (`localebridge.validators.plural`) checks that each translated message
carries the plural categories its target locale requires under Unicode CLDR.

## Supported syntax

### Simple arguments

```
Hello {name}
```

The placeholder is preserved verbatim through translation.

### Plurals

```
{count, plural, one {You have # new message} other {You have # new messages}}
```

When the source contains a plural block, the translator expands it into all the
plural categories the target locale needs. The category set per locale:

| Locale | Categories | Count |
|--------|------------|-------|
| en, es, de, hi | one, other | 2 |
| fr | one, many, other | 3 |
| ru, pl | one, few, many, other | 4 |
| ar | zero, one, two, few, many, other | 6 |
| ja, zh-CN | other | 1 |

A translation missing a required category is flagged `PLURAL_MISSING_CATEGORY`.

#### Worked example: Russian (4 categories)

Source (English, 2 categories):

```
{count, plural, one {You have # new message} other {You have # new messages}}
```

Russian output (4 categories: `one`, `few`, `many`, `other`):

```
{count, plural, one {You have # new message} few {You have # new messages} many {You have # new messages} other {You have # new messages}}
```

#### Worked example: Arabic (6 categories)

```
{count, plural, zero {...} one {...} two {...} few {...} many {...} other {...}}
```

All six CLDR categories are emitted; `validate_plural_coverage` then passes.

### Select

```
{gender, select, male {He invited you} female {She invited you} other {They invited you}}
```

The branch keywords and structure are preserved through translation.

### Nested arguments

A placeholder may appear inside a plural or select branch:

```
{count, plural, one {{name} sent you a message} other {{name} sent you # messages}}
```

The nested `{name}` survives in every expanded branch.

### Exact-match plural branches

```
{count, plural, =0 {none} one {1} other {# items}}
```

`=N` exact-match branches are accepted by the validator.

## Not supported

These are intentionally out of scope; the validator does not special-case them
and the translator passes their argument blocks through unchanged:

- Relative dates / `{ts, date, relative}` style relative formatting.
- ICU number skeletons (`{value, number, ::currency/EUR}`).
- `selectordinal` is parsed structurally but not expanded by category.
- Locale-specific formatting of numbers/dates inside `#` (the literal `#` is
  preserved, not localized).

## Validation codes

| Code | Meaning |
|------|---------|
| `ICU_PARSE` | The message is not well-formed ICU MessageFormat. |
| `PLURAL_MISSING_CATEGORY` | A required CLDR plural category is absent. |
| `PLURAL_UNKNOWN_LOCALE` | No CLDR plural rules registered for the locale. |
