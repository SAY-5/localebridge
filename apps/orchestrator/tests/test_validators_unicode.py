"""Unicode safety: NFC, bidi, zero-width."""

from __future__ import annotations

from localebridge.validators.unicode import to_nfc, validate_unicode


def test_clean_ascii_passes() -> None:
    assert validate_unicode("k", "en", "Hello world") == []


def test_bidi_control_flagged_as_error() -> None:
    text = "admin‮txt.exe"  # right-to-left override
    issues = validate_unicode("k", "en", text)
    codes = [i.code for i in issues]
    assert "UNICODE_BIDI_CONTROL" in codes
    assert any(i.severity == "error" for i in issues if i.code == "UNICODE_BIDI_CONTROL")


def test_zero_width_warned() -> None:
    text = "hello​world"
    issues = validate_unicode("k", "en", text)
    assert any(i.code == "UNICODE_ZERO_WIDTH" for i in issues)


def test_decomposed_form_warned() -> None:
    # é as e + combining acute
    text = "café"
    issues = validate_unicode("k", "en", text)
    assert any(i.code == "UNICODE_NOT_NFC" for i in issues)


def test_to_nfc_is_idempotent() -> None:
    s = "café"
    once = to_nfc(s)
    twice = to_nfc(once)
    assert once == twice
