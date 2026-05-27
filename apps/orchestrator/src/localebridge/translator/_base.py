"""Translator protocol."""

from __future__ import annotations

from typing import Protocol


class Translator(Protocol):
    def translate(
        self, key: str, source_text: str, target_locale: str, *, note: str | None = None
    ) -> str:
        """Translate `source_text` from the source locale into `target_locale`.

        `note` carries optional reviewer feedback (e.g. a reject reason) so a
        retranslation can take it into account.

        Implementations must be pure functions of their inputs to keep CI
        hermetic when the FakeTranslator is in use.
        """
        ...
