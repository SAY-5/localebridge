"""Plural-rule coverage per CLDR.

For each locale, the set of plural categories that MUST appear when a source
string contains `{count, plural, ...}`. Values reflect Unicode CLDR rules.
"""

from __future__ import annotations

import re

from ..models import ValidationIssue

# Subset of CLDR plural categories per locale, sufficient for the locales we ship.
CLDR_PLURAL_CATEGORIES: dict[str, frozenset[str]] = {
    "en": frozenset({"one", "other"}),
    "es": frozenset({"one", "other"}),
    "de": frozenset({"one", "other"}),
    "fr": frozenset({"one", "many", "other"}),
    "ja": frozenset({"other"}),
    "zh-CN": frozenset({"other"}),
    "ar": frozenset({"zero", "one", "two", "few", "many", "other"}),
    "hi": frozenset({"one", "other"}),
    "ru": frozenset({"one", "few", "many", "other"}),
    "pl": frozenset({"one", "few", "many", "other"}),
}

_PLURAL_OPEN_RE = re.compile(r"\{([A-Za-z_][\w-]*)\s*,\s*plural\s*,")
_BRANCH_KW_RE = re.compile(r"(=?\w+)\s*\{")


def source_has_plural(text: str) -> bool:
    return bool(_PLURAL_OPEN_RE.search(text))


def categories_present(text: str) -> set[str]:
    """Return the set of plural-category keywords present in any plural block."""
    out: set[str] = set()
    for m in _PLURAL_OPEN_RE.finditer(text):
        start = m.end()
        depth = 1
        i = start
        # walk the plural block until matching '}'
        while i < len(text) and depth > 0:
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            i += 1
        block = text[start:i - 1]
        for bm in _BRANCH_KW_RE.finditer(block):
            kw = bm.group(1)
            if kw.startswith("="):
                continue
            if kw in {"plural", "select", "selectordinal", "offset"}:
                continue
            out.add(kw)
    return out


def validate_plural_coverage(
    key: str,
    locale: str,
    source_text: str,
    translated_text: str,
) -> list[ValidationIssue]:
    """Every required CLDR plural category for `locale` must be present
    when the source contains a plural block."""
    if not source_has_plural(source_text):
        return []
    required = CLDR_PLURAL_CATEGORIES.get(locale)
    if required is None:
        return [
            ValidationIssue(
                severity="warning",
                code="PLURAL_UNKNOWN_LOCALE",
                message=f"No CLDR plural rules registered for locale {locale!r}",
                key=key,
                locale=locale,
            )
        ]
    present = categories_present(translated_text)
    missing = required - present
    issues: list[ValidationIssue] = []
    for cat in sorted(missing):
        issues.append(
            ValidationIssue(
                severity="error",
                code="PLURAL_MISSING_CATEGORY",
                message=f"Locale {locale} requires plural category {cat!r}",
                key=key,
                locale=locale,
            )
        )
    return issues
