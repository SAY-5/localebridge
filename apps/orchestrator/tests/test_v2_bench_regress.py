"""Regression-gate logic tests for the bench harness."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from localebridge import bench
from localebridge.bench import BenchResult, regress

_FAST = BenchResult(
    n=500,
    files=20,
    extraction_seconds=0.1,
    extraction_files_per_sec=200.0,
    extraction_strings_per_sec=5000.0,
    extraction_peak_mb=1.0,
    translation_seconds=0.01,
    translation_per_sec=400000.0,
    icu_validations_per_sec=600000.0,
    plural_validations_per_sec=4000000.0,
    unicode_validations_per_sec=1200000.0,
    length_validations_per_sec=4000000.0,
)


def _slow_of(base: BenchResult, factor: float) -> BenchResult:
    d = asdict(base)
    for k in list(d):
        if k.endswith("_per_sec"):
            d[k] = d[k] * factor
    return BenchResult(**d)


@pytest.fixture
def patched_baseline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "bench_baseline.json"
    monkeypatch.setattr(bench, "BASELINE_PATH", path)
    return path


def test_regress_seeds_baseline_when_missing(
    patched_baseline: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bench, "run_bench", lambda n, files: _FAST)
    rc = regress(threshold=0.30, n=500, files=20)
    assert rc == 0
    assert patched_baseline.exists()
    seeded = json.loads(patched_baseline.read_text())
    assert seeded["n"] == 500


def test_regress_passes_within_threshold(
    patched_baseline: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patched_baseline.write_text(json.dumps(asdict(_FAST)))
    # 10% slower is inside the 30% gate.
    monkeypatch.setattr(bench, "run_bench", lambda n, files: _slow_of(_FAST, 0.90))
    assert regress(threshold=0.30, n=500, files=20) == 0


def test_regress_fails_on_throughput_drop(
    patched_baseline: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patched_baseline.write_text(json.dumps(asdict(_FAST)))
    # Half the throughput trips every axis.
    monkeypatch.setattr(bench, "run_bench", lambda n, files: _slow_of(_FAST, 0.50))
    assert regress(threshold=0.30, n=500, files=20) == 1
