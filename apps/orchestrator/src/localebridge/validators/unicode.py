"""Unicode safety: NFC normalization + bidi-control + zero-width detection."""

from __future__ import annotations

import unicodedata

from ..models import ValidationIssue

# Bidi control characters that can flip rendering direction (Trojan Source class).
_BIDI_CONTROLS = frozenset(
    chr(c) for c in (
        0x202A, 0x202B, 0x202C, 0x202D, 0x202E,  # LRE/RLE/PDF/LRO/RLO
        0x2066, 0x2067, 0x2068, 0x2069,           # LRI/RLI/FSI/PDI
    )
)

# Zero-width and BOM-style characters that can hide content.
_ZERO_WIDTH = frozenset(chr(c) for c in (0x200B, 0x200C, 0x200D, 0xFEFF))


def validate_unicode(
    key: str,
    locale: str,
    text: str,
    *,
    allow_bidi: bool = False,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    nfc = unicodedata.normalize("NFC", text)
    if nfc != text:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="UNICODE_NOT_NFC",
                message="String is not in NFC normalization form",
                key=key,
                locale=locale,
            )
        )
    bidi_hits = [c for c in text if c in _BIDI_CONTROLS]
    if bidi_hits and not allow_bidi:
        issues.append(
            ValidationIssue(
                severity="error",
                code="UNICODE_BIDI_CONTROL",
                message=(
                    f"Bidi-control characters found ({len(bidi_hits)}); "
                    "this can hide malicious text in source files"
                ),
                key=key,
                locale=locale,
            )
        )
    zw_hits = [c for c in text if c in _ZERO_WIDTH]
    if zw_hits:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="UNICODE_ZERO_WIDTH",
                message=f"Zero-width characters found ({len(zw_hits)})",
                key=key,
                locale=locale,
            )
        )
    return issues


def to_nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)
