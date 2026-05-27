"""v3: complex ICU MessageFormat translate + validate.

Proves that a source ICU plural/select/nested message survives translation
through the FakeTranslator and comes out valid for each target locale, with the
plural categories the locale's CLDR rules require.
"""

from __future__ import annotations

import pytest

from localebridge.translator import FakeTranslator
from localebridge.validators.icu import validate_icu
from localebridge.validators.plural import (
    CLDR_PLURAL_CATEGORIES,
    categories_present,
    validate_plural_coverage,
)

PLURAL_SRC = "{count, plural, one {You have # new message} other {You have # new messages}}"
SELECT_SRC = "{gender, select, male {He invited you} female {She invited you} other {They invited you}}"
NESTED_SRC = (
    "{count, plural, "
    "one {{name} sent you a message} "
    "other {{name} sent you # messages}}"
)


@pytest.fixture
def translator() -> FakeTranslator:
    return FakeTranslator()


@pytest.mark.parametrize(
    "locale,n_categories",
    [("en", 2), ("ru", 4), ("ar", 6)],
)
def test_plural_translates_and_validates(
    translator: FakeTranslator, locale: str, n_categories: int
) -> None:
    out = translator.translate("inbox.count", PLURAL_SRC, locale)
    assert validate_icu("inbox.count", locale, out) == []
    assert validate_plural_coverage("inbox.count", locale, PLURAL_SRC, out) == []
    present = categories_present(out)
    assert present == CLDR_PLURAL_CATEGORIES[locale]
    assert len(present) == n_categories


def test_russian_has_exactly_four_categories(translator: FakeTranslator) -> None:
    out = translator.translate("inbox.count", PLURAL_SRC, "ru")
    assert categories_present(out) == {"one", "few", "many", "other"}


def test_arabic_has_all_six_categories(translator: FakeTranslator) -> None:
    out = translator.translate("inbox.count", PLURAL_SRC, "ar")
    assert categories_present(out) == {"zero", "one", "two", "few", "many", "other"}


@pytest.mark.parametrize("locale", ["en", "fr", "de", "ru", "ar", "ja", "zh-CN", "hi"])
def test_select_structure_survives(translator: FakeTranslator, locale: str) -> None:
    out = translator.translate("invite.line", SELECT_SRC, locale)
    assert validate_icu("invite.line", locale, out) == []
    assert "select" in out
    for kw in ("male", "female", "other"):
        assert kw in out


@pytest.mark.parametrize("locale", ["en", "ru", "ar"])
def test_nested_arg_inside_plural_survives(translator: FakeTranslator, locale: str) -> None:
    out = translator.translate("inbox.from", NESTED_SRC, locale)
    assert validate_icu("inbox.from", locale, out) == []
    assert validate_plural_coverage("inbox.from", locale, NESTED_SRC, out) == []
    # the nested {name} placeholder must survive in every produced branch
    assert "{name}" in out


def test_idempotent_retranslation(translator: FakeTranslator) -> None:
    once = translator.translate("inbox.count", PLURAL_SRC, "ru")
    twice = translator.translate("inbox.count", once, "ru")
    assert categories_present(twice) == CLDR_PLURAL_CATEGORIES["ru"]
    assert validate_icu("inbox.count", "ru", twice) == []
