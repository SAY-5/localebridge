"""Plural-coverage decision-table tests."""

from __future__ import annotations

from localebridge.validators.plural import (
    CLDR_PLURAL_CATEGORIES,
    categories_present,
    source_has_plural,
    validate_plural_coverage,
)

EN_PLURAL = "{count, plural, one {1 item} other {# items}}"
RU_PLURAL = "{count, plural, one {1} few {2} many {5} other {x}}"
AR_PLURAL = "{count, plural, zero {0} one {1} two {2} few {f} many {m} other {x}}"


def test_source_has_plural_detects_keyword() -> None:
    assert source_has_plural(EN_PLURAL)
    assert not source_has_plural("Hello world")


def test_categories_present_extracts_branch_keywords() -> None:
    cats = categories_present(EN_PLURAL)
    assert cats == {"one", "other"}


def test_english_required_categories_satisfied() -> None:
    issues = validate_plural_coverage("k", "en", EN_PLURAL, EN_PLURAL)
    assert issues == []


def test_russian_requires_four_categories() -> None:
    # Translate to Russian but only emit two categories: must flag missing.
    only_two = "{count, plural, one {1} other {x}}"
    issues = validate_plural_coverage("k", "ru", EN_PLURAL, only_two)
    missing = {i.message.rsplit("'", 2)[1] for i in issues}
    assert "few" in missing
    assert "many" in missing


def test_arabic_full_six_categories() -> None:
    issues = validate_plural_coverage("k", "ar", EN_PLURAL, AR_PLURAL)
    assert issues == []


def test_japanese_only_other() -> None:
    issues = validate_plural_coverage("k", "ja", EN_PLURAL, "{count, plural, other {x}}")
    assert issues == []


def test_unknown_locale_warns() -> None:
    issues = validate_plural_coverage("k", "xx", EN_PLURAL, "{count, plural, other {x}}")
    assert any(i.code == "PLURAL_UNKNOWN_LOCALE" for i in issues)


def test_all_known_locales_have_categories() -> None:
    for locale, cats in CLDR_PLURAL_CATEGORIES.items():
        assert "other" in cats, f"locale {locale} missing required 'other' category"
