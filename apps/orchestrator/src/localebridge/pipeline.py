"""End-to-end pipeline: extracted strings -> translations -> validation -> write."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ExtractedString, Translation, ValidationReport
from .tm import InMemoryTM
from .translator import FakeTranslator, Translator
from .validators import validate_icu, validate_length, validate_plural_coverage, validate_unicode
from .writer import write_locales

DEFAULT_LOCALES = ("es", "fr", "de", "ja", "ar", "zh-CN", "hi")


def run(
    extracted_path: str | Path,
    out_locales_dir: str | Path,
    *,
    targets: tuple[str, ...] = DEFAULT_LOCALES,
    translator: Translator | None = None,
    tm: InMemoryTM | None = None,
    review_mode: bool = False,
) -> tuple[ValidationReport, dict[str, int]]:
    """Run the pipeline. Returns (validation_report, write_counts).

    Translation-memory reuse rules (this is how the human-review queue
    "remembers" a reviewer's decision across runs):

      - `edited` or `approved` cached entries are reused verbatim and never
        re-sent to the translator (no re-LLM-call).
      - `rejected` cached entries are re-translated; the reviewer's reject
        reason is passed back to the translator as context.
      - missing entries are translated fresh. In `review_mode` they enter as
        `pending_review` (so they surface in the queue) instead of auto-approved.
    """
    translator = translator or FakeTranslator()
    tm = tm or InMemoryTM()
    raw = json.loads(Path(extracted_path).read_text(encoding="utf-8"))
    extracted = [ExtractedString.model_validate(e) for e in raw]
    translations: list[Translation] = []
    for e in extracted:
        for locale in targets:
            cached = tm.get(e.key, locale)
            if cached is not None and cached.status in ("edited", "approved", "pending_review"):
                translations.append(cached)
                continue
            note = cached.reject_reason if cached is not None else None
            txt = translator.translate(e.key, e.default_value, locale, note=note)
            t = Translation(
                key=e.key,
                locale=locale,
                source_text=e.default_value,
                translated_text=txt,
                status="pending_review" if review_mode else "approved",
            )
            tm.put(t)
            translations.append(t)
    report = validate_all(extracted, translations)
    counts = write_locales(out_locales_dir, translations)
    return report, counts


def validate_all(
    extracted: list[ExtractedString], translations: list[Translation]
) -> ValidationReport:
    report = ValidationReport()
    source_by_key = {e.key: e.default_value for e in extracted}
    for t in translations:
        src = source_by_key.get(t.key, t.source_text)
        report.issues.extend(validate_icu(t.key, t.locale, t.translated_text))
        report.issues.extend(validate_unicode(t.key, t.locale, t.translated_text))
        report.issues.extend(validate_plural_coverage(t.key, t.locale, src, t.translated_text))
        report.issues.extend(validate_length(t.key, t.locale, src, t.translated_text))
    return report
