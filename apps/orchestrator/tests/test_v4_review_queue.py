"""v4: human-review queue, diff-and-approve, and translation-memory recall.

The headline guarantee: once a reviewer edits a translation, the next pipeline
run reuses the edit and never calls the translator again for that key/locale.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from fastapi.testclient import TestClient

from localebridge.api import create_app
from localebridge.models import Translation
from localebridge.pipeline import run
from localebridge.tm import InMemoryTM


@dataclass
class CountingTranslator:
    """Wraps a fixed output and records every (key, locale) it is asked to translate."""

    calls: list[tuple[str, str]] = field(default_factory=list)

    def translate(
        self, key: str, source_text: str, target_locale: str, *, note: str | None = None
    ) -> str:
        self.calls.append((key, target_locale))
        suffix = f" [redo:{note}]" if note else ""
        return f"AI({target_locale}):{source_text}{suffix}"


def _write_extracted(tmp_path: Path) -> Path:
    p = tmp_path / "extracted.json"
    p.write_text(
        json.dumps(
            [
                {
                    "key": "nav.home",
                    "default_value": "Home",
                    "source_file": "Nav.tsx",
                    "line": 1,
                    "context": "t-call",
                }
            ]
        )
    )
    return p


def test_queue_surfaces_pending_with_warnings() -> None:
    tm = InMemoryTM()
    tm.put(
        Translation(
            key="inbox.count",
            locale="ru",
            source_text="{count, plural, one {# msg} other {# msgs}}",
            # deliberately missing ru categories -> validator warnings
            translated_text="{count, plural, one {# msg}}",
            status="pending_review",
        )
    )
    client = TestClient(create_app(tm))
    queue = client.get("/v1/queue").json()
    assert len(queue) == 1
    item = queue[0]
    assert item["source"].startswith("{count")
    assert item["ai_translation"] == "{count, plural, one {# msg}}"
    codes = {w["code"] for w in item["validator_warnings"]}
    assert "PLURAL_MISSING_CATEGORY" in codes


def test_edit_is_remembered_and_skips_retranslation(tmp_path: Path) -> None:
    extracted = _write_extracted(tmp_path)
    locales = tmp_path / "locales"
    tm = InMemoryTM()
    translator = CountingTranslator()

    # First run in review mode: one fresh translation, entered as pending.
    run(extracted, locales, targets=("es",), translator=translator, tm=tm, review_mode=True)
    assert translator.calls == [("nav.home", "es")]
    assert tm.get("nav.home", "es").status == "pending_review"

    # Reviewer edits via the API.
    client = TestClient(create_app(tm))
    r = client.post(
        "/v1/translations/es/nav.home/review",
        json={"action": "edit", "edited_text": "Inicio (revisado)", "reason": "house style"},
    )
    assert r.status_code == 200, r.text
    assert tm.get("nav.home", "es").status == "edited"

    # Second run: the edit is reused, the translator is NOT called again.
    translator.calls.clear()
    run(extracted, locales, targets=("es",), translator=translator, tm=tm, review_mode=True)
    assert translator.calls == [], "edited entry must not be re-translated"

    written = json.loads((locales / "es.json").read_text())
    assert written["nav.home"] == "Inicio (revisado)"


def test_reject_sends_back_to_translator_with_note(tmp_path: Path) -> None:
    extracted = _write_extracted(tmp_path)
    locales = tmp_path / "locales"
    tm = InMemoryTM()
    translator = CountingTranslator()

    run(extracted, locales, targets=("es",), translator=translator, tm=tm, review_mode=True)

    client = TestClient(create_app(tm))
    client.post(
        "/v1/translations/es/nav.home/review",
        json={"action": "reject", "reason": "wrong register"},
    )
    assert tm.get("nav.home", "es").status == "rejected"

    translator.calls.clear()
    run(extracted, locales, targets=("es",), translator=translator, tm=tm, review_mode=True)
    # rejected -> re-translated, and the reject note is handed back to the translator
    assert translator.calls == [("nav.home", "es")]
    assert "redo:wrong register" in tm.get("nav.home", "es").translated_text


def test_approved_entry_is_reused(tmp_path: Path) -> None:
    extracted = _write_extracted(tmp_path)
    locales = tmp_path / "locales"
    tm = InMemoryTM()
    translator = CountingTranslator()

    run(extracted, locales, targets=("es",), translator=translator, tm=tm, review_mode=True)
    client = TestClient(create_app(tm))
    client.post("/v1/translations/es/nav.home/review", json={"action": "approve"})

    translator.calls.clear()
    run(extracted, locales, targets=("es",), translator=translator, tm=tm, review_mode=True)
    assert translator.calls == []
