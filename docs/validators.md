# Validators

Four validators run against every (key, locale, translated_text) tuple.

## ICU MessageFormat

Implemented as a recursive-descent parser in `localebridge.validators.icu`. The grammar accepted is:

```
message     = ( literal | placeholder )*
placeholder = '{' ID ( ',' TYPE ( ',' STYLE )? )? '}'
TYPE        = plural | select | selectordinal | number | date | time
STYLE       = ( WORD '{' message '}' )+
```

Returns one error per parse failure. Recognized types are validated; unknown types are rejected (`{count, totallyfake, ...}`).

## Plural coverage

Sources containing `{var, plural, ...}` blocks require the target locale's CLDR plural categories to all appear in the translation. The category set per locale comes from `CLDR_PLURAL_CATEGORIES`:

| Locale | Required categories |
|---|---|
| en, es, de, hi | one, other |
| fr | one, many, other |
| ja, zh-CN | other |
| ar | zero, one, two, few, many, other |
| ru, pl | one, few, many, other |

Missing categories raise an error per category. Unknown locales raise a warning.

## Unicode safety

- `UNICODE_NOT_NFC` (warning): string is not in NFC normalization form
- `UNICODE_BIDI_CONTROL` (error): the string contains U+202A through U+202E or U+2066 through U+2069, the Trojan-Source class
- `UNICODE_ZERO_WIDTH` (warning): the string contains U+200B through U+200D or U+FEFF

The bidi check is the security-load-bearing one: an attacker can embed RLO/LRO to make a string render differently from its byte content. Allowed only when the caller passes `allow_bidi=True`.

## Length budget

`LENGTH_OVERFLOW` (warning) if the translation is more than 1.5x the source length. UI overflow risk warning, not a merge-blocker.
