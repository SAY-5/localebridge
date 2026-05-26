"""v1 plural-coverage decision table.

For every (source-has-plural x target-locale x translated-categories) cell,
assert the validator's classification.
"""

from __future__ import annotations

from itertools import product

import pytest

from localebridge.validators.plural import CLDR_PLURAL_CATEGORIES, validate_plural_coverage

LOCALES = ["en", "es", "de", "fr", "ja", "zh-CN", "ar", "hi", "ru", "pl"]
ALL_CATEGORIES = ["zero", "one", "two", "few", "many", "other"]

EN_PLURAL_SRC = "{count, plural, one {1} other {x}}"
NON_PLURAL_SRC = "Hello"


def _translated_with_categories(cats: frozenset[str]) -> str:
    body = " ".join(f"{c} {{x}}" for c in sorted(cats))
    return "{count, plural, " + body + "}"


@pytest.mark.parametrize("locale", LOCALES)
def test_full_coverage_passes(locale: str) -> None:
    required = CLDR_PLURAL_CATEGORIES[locale]
    translated = _translated_with_categories(required)
    issues = validate_plural_coverage("k", locale, EN_PLURAL_SRC, translated)
    assert issues == []


@pytest.mark.parametrize("locale", LOCALES)
def test_zero_coverage_fails(locale: str) -> None:
    required = CLDR_PLURAL_CATEGORIES[locale]
    if required == frozenset({"other"}):
        # ja/zh-CN only need "other"; "empty" body still has no "other".
        translated = "{count, plural, one {x}}"
        issues = validate_plural_coverage("k", locale, EN_PLURAL_SRC, translated)
        assert any(i.code == "PLURAL_MISSING_CATEGORY" for i in issues)
    else:
        translated = "{count, plural, one {x}}"
        issues = validate_plural_coverage("k", locale, EN_PLURAL_SRC, translated)
        # Expect at least one missing category (since "one" alone doesn't cover the full set)
        codes = [i.code for i in issues]
        assert "PLURAL_MISSING_CATEGORY" in codes


def test_non_plural_source_never_flags() -> None:
    for locale in LOCALES:
        issues = validate_plural_coverage("k", locale, NON_PLURAL_SRC, "anything")
        assert issues == []


def _decision_table_size() -> int:
    """The decision table covers every (locale, subset of categories) pair."""
    # For each locale: 2^|all_categories| subsets => count assertions we'd cover.
    return len(LOCALES) * (2 ** len(ALL_CATEGORIES))


@pytest.mark.parametrize("locale,cats", [
    (loc, frozenset(c for c, keep in zip(ALL_CATEGORIES, mask, strict=True) if keep))
    for loc, mask in product(LOCALES, product([False, True], repeat=len(ALL_CATEGORIES)))
])
def test_decision_table_classification(locale: str, cats: frozenset[str]) -> None:
    """Every (locale, category-subset) cell: validator agrees with set comparison."""
    required = CLDR_PLURAL_CATEGORIES[locale]
    translated = _translated_with_categories(cats) if cats else "{count, plural,}"
    issues = validate_plural_coverage("k", locale, EN_PLURAL_SRC, translated)
    missing = required - cats
    error_codes = [i for i in issues if i.code == "PLURAL_MISSING_CATEGORY"]
    if missing:
        assert error_codes, f"expected missing {missing} to be flagged for {locale}"
    else:
        assert not error_codes, f"unexpected flags for {locale}/{cats}: {issues}"


def test_decision_table_size_documented() -> None:
    # Exposed so README can cite it.
    assert _decision_table_size() == 640
