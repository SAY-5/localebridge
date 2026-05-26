"""Write per-locale JSON files back to disk."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Translation


def write_locales(out_dir: str | Path, translations: list[Translation]) -> dict[str, int]:
    """Group translations by locale, write `<out_dir>/<locale>.json`.

    Returns: a dict of {locale: count} for the caller to log.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    by_locale: dict[str, dict[str, str]] = {}
    for t in translations:
        if t.status == "rejected":
            continue
        by_locale.setdefault(t.locale, {})[t.key] = t.translated_text
    counts: dict[str, int] = {}
    for locale, mapping in sorted(by_locale.items()):
        path = out / f"{locale}.json"
        sorted_map = {k: mapping[k] for k in sorted(mapping)}
        path.write_text(json.dumps(sorted_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        counts[locale] = len(sorted_map)
    return counts
