"""Claude-shaped translator stub.

This is intentionally not wired to the network. It documents the shape of a
real provider and provides a sandboxed `translate` that raises unless the
operator explicitly opts in by setting `LOCALEBRIDGE_LIVE_LLM=1`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ClaudeProvider:
    model: str = "claude-opus-4-7"

    def translate(
        self, key: str, source_text: str, target_locale: str, *, note: str | None = None
    ) -> str:
        if os.environ.get("LOCALEBRIDGE_LIVE_LLM") != "1":
            raise RuntimeError(
                "ClaudeProvider.translate called but LOCALEBRIDGE_LIVE_LLM is not set. "
                "Use FakeTranslator for tests; set LOCALEBRIDGE_LIVE_LLM=1 to opt in."
            )
        # Real implementation would call anthropic.Anthropic().messages.create.
        # Kept as a stub here so CI is hermetic.
        raise NotImplementedError("Live provider intentionally not wired in this repo")
