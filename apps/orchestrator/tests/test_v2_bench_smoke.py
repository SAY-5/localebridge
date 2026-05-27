"""Smoke test for the bench harness at small N."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from localebridge.bench import run_bench

REPO_ROOT = Path(__file__).resolve().parents[3]
EXTRACTOR_CLI = REPO_ROOT / "apps" / "extractor" / "dist" / "cli.js"


@pytest.fixture(scope="module", autouse=True)
def ensure_extractor_built() -> None:
    if EXTRACTOR_CLI.exists():
        return
    if shutil.which("pnpm") is None:
        pytest.skip("pnpm not available, skipping bench smoke test")
    subprocess.run(
        ["pnpm", "--filter", "./apps/extractor", "build"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )


def test_bench_smoke_n_500() -> None:
    result = run_bench(n=500, files=20)
    assert result.n == 500
    assert result.files == 20
    # sanity floors: even on slowest CI we should comfortably clear these
    assert result.extraction_strings_per_sec > 50
    assert result.translation_per_sec > 1000
    assert result.icu_validations_per_sec > 1000
    assert result.unicode_validations_per_sec > 1000
