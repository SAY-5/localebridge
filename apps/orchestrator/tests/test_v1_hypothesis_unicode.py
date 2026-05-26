"""Property tests for the Unicode safety validator (v1)."""

from __future__ import annotations

import unicodedata

from hypothesis import given, settings
from hypothesis import strategies as st

from localebridge.validators.unicode import to_nfc, validate_unicode

text_any = st.text(min_size=0, max_size=80)


@given(text_any)
@settings(max_examples=400, deadline=None)
def test_nfc_idempotent(s: str) -> None:
    once = to_nfc(s)
    twice = to_nfc(once)
    assert once == twice


@given(text_any)
@settings(max_examples=400, deadline=None)
def test_nfc_result_is_nfc(s: str) -> None:
    out = to_nfc(s)
    assert unicodedata.is_normalized("NFC", out)


_BIDI_CTRLS = ["‪", "‫", "‬", "‭", "‮",
               "⁦", "⁧", "⁨", "⁩"]


@given(st.sampled_from(_BIDI_CTRLS), text_any, text_any)
@settings(max_examples=200, deadline=None)
def test_every_bidi_ctrl_is_flagged(ctrl: str, before: str, after: str) -> None:
    text = f"{before}{ctrl}{after}"
    issues = validate_unicode("k", "en", text)
    assert any(i.code == "UNICODE_BIDI_CONTROL" and i.severity == "error" for i in issues)


_ZW = ["​", "‌", "‍", "﻿"]


@given(st.sampled_from(_ZW), text_any, text_any)
@settings(max_examples=200, deadline=None)
def test_every_zero_width_is_flagged(ctrl: str, before: str, after: str) -> None:
    text = f"{before}{ctrl}{after}"
    issues = validate_unicode("k", "en", text)
    assert any(i.code == "UNICODE_ZERO_WIDTH" for i in issues)


@given(text_any.filter(lambda s: all(c not in _BIDI_CTRLS + _ZW for c in s)))
@settings(max_examples=400, deadline=None)
def test_clean_text_has_no_security_errors(s: str) -> None:
    # NFC warnings allowed; bidi/zw errors must not appear.
    issues = validate_unicode("k", "en", s)
    sec_errors = [i for i in issues if i.code in {"UNICODE_BIDI_CONTROL", "UNICODE_ZERO_WIDTH"}]
    assert sec_errors == []
