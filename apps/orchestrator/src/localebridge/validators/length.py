"""Length-budget validator: warn when translation overflows source by >50%."""

from __future__ import annotations

from ..models import ValidationIssue


def validate_length(
    key: str,
    locale: str,
    source_text: str,
    translated_text: str,
    *,
    threshold: float = 1.5,
) -> list[ValidationIssue]:
    if not source_text:
        return []
    ratio = len(translated_text) / len(source_text)
    if ratio > threshold:
        return [
            ValidationIssue(
                severity="warning",
                code="LENGTH_OVERFLOW",
                message=(
                    f"Translation is {ratio:.2f}x the source length "
                    f"(>{threshold:.2f}); UI overflow likely"
                ),
                key=key,
                locale=locale,
            )
        ]
    return []
