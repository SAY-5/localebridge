"""End-to-end pipeline test: extracted JSON -> translation -> validation -> locale files."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from localebridge.pipeline import run


@pytest.fixture()
def extracted_file(tmp_path: Path) -> Path:
    data = [
        {
            "key": "nav.home",
            "default_value": "Home",
            "source_file": "src/Nav.tsx",
            "line": 4,
            "context": "t-call",
        },
        {
            "key": "settings.title",
            "default_value": "Settings",
            "source_file": "src/Settings.tsx",
            "line": 5,
            "context": "t-call",
        },
    ]
    p = tmp_path / "extracted.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_pipeline_writes_locale_files(extracted_file: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "locales"
    report, counts = run(extracted_file, out_dir, targets=("es", "fr", "ja"))
    assert not report.has_errors
    assert counts == {"es": 2, "fr": 2, "ja": 2}
    es = json.loads((out_dir / "es.json").read_text())
    assert es["nav.home"] == "Inicio"
    assert es["settings.title"] == "Ajustes"
    ja = json.loads((out_dir / "ja.json").read_text())
    assert ja["nav.home"] == "ホーム"
