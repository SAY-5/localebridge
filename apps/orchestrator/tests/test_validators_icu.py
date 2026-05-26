"""Unit tests for the ICU MessageFormat validator."""

from __future__ import annotations

import pytest

from localebridge.validators.icu import validate_icu

VALID = [
    "Hello",
    "Hello {name}",
    "{count, plural, one {1 item} other {# items}}",
    "{gender, select, male {his} female {her} other {their}}",
    "{count, plural, one {1 {item}} other {# {items}}}",
    "{count, plural, =0 {none} one {1} other {many}}",
]

INVALID = [
    "Hello {",
    "Hello }name{",
    "{name",
    "{count, totallyfake, one {x} other {y}}",
    "{,plural,one{x}other{y}}",
    "{count, plural, one x other y}",
]


@pytest.mark.parametrize("text", VALID)
def test_valid_icu_passes(text: str) -> None:
    issues = validate_icu("k", "en", text)
    assert issues == [], f"unexpected issues for {text!r}: {issues}"


@pytest.mark.parametrize("text", INVALID)
def test_invalid_icu_flagged(text: str) -> None:
    issues = validate_icu("k", "en", text)
    assert any(i.code == "ICU_PARSE" for i in issues), f"missed invalid {text!r}"
