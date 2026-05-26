from __future__ import annotations

from localebridge.validators.length import validate_length


def test_short_translation_no_warning() -> None:
    assert validate_length("k", "es", "Hello", "Hola") == []


def test_overflow_warning() -> None:
    # 2x the source length should warn
    src = "Save"
    tr = "Speichern Sie Ihre Änderungen jetzt"
    issues = validate_length("k", "de", src, tr)
    assert any(i.code == "LENGTH_OVERFLOW" for i in issues)


def test_empty_source_skipped() -> None:
    assert validate_length("k", "en", "", "anything") == []
