"""Bench harness for LocaleBridge.

Three axes:
  1. Extraction throughput  (strings/sec, files/sec) -- runs the TS extractor
     against a synthesized React app with N translatable keys.
  2. Translation throughput  (translations/sec) -- runs the FakeTranslator
     against the extracted strings across all default target locales.
  3. Validation throughput  (validations/sec, per axis: icu, plural, unicode, length).

`bench-regress` compares current results to a stored baseline and fails the
process if any axis drifts beyond `--threshold` (default 30%).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import ExtractedString, Translation
from .pipeline import DEFAULT_LOCALES, validate_all
from .translator import FakeTranslator

REPO_ROOT = Path(__file__).resolve().parents[4]
EXTRACTOR_CLI = REPO_ROOT / "apps" / "extractor" / "dist" / "cli.js"
BASELINE_PATH = REPO_ROOT / "apps" / "orchestrator" / "bench_baseline.json"


@dataclass(slots=True)
class BenchResult:
    n: int
    files: int
    extraction_seconds: float
    extraction_files_per_sec: float
    extraction_strings_per_sec: float
    extraction_peak_mb: float
    translation_seconds: float
    translation_per_sec: float
    icu_validations_per_sec: float
    plural_validations_per_sec: float
    unicode_validations_per_sec: float
    length_validations_per_sec: float


def synthesize_react_app(out: Path, n: int, files: int) -> None:
    """Create `files` .tsx files containing roughly n/files translatable strings each."""
    out.mkdir(parents=True, exist_ok=True)
    per_file = max(1, n // files)
    counter = 0
    for f in range(files):
        body_lines = []
        for _ in range(per_file):
            if counter >= n:
                break
            body_lines.append(
                f'      <span>{{t("k.{counter}", {{ defaultValue: "Hello {counter}" }})}}</span>'
            )
            counter += 1
        body = "\n".join(body_lines)
        (out / f"f{f}.tsx").write_text(
            "import { useTranslation } from \"react-i18next\";\n"
            f"export function F{f}() {{\n"
            "  const { t } = useTranslation();\n"
            "  return (\n    <div>\n"
            f"{body}\n"
            "    </div>\n  );\n}\n",
            encoding="utf-8",
        )


def measure_extraction(src: Path) -> tuple[float, int, int, float]:
    """Return (seconds, files_scanned, strings_extracted, peak_mb)."""
    if not EXTRACTOR_CLI.exists():
        raise RuntimeError(
            f"Extractor not built: {EXTRACTOR_CLI} missing. Run `pnpm --filter ./apps/extractor build`."
        )
    out_json = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    out_json.close()
    tracemalloc.start()
    t0 = time.perf_counter()
    result = subprocess.run(
        ["node", str(EXTRACTOR_CLI), "--src", str(src), "--out", out_json.name],
        check=True,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - t0
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    data = json.loads(Path(out_json.name).read_text(encoding="utf-8"))
    os.unlink(out_json.name)
    files = len(list(src.glob("*.tsx")))
    # parse extractor stderr/stdout for the count it reported
    _ = result.stdout
    return elapsed, files, len(data), peak / (1024 * 1024)


def measure_translation(extracted: list[ExtractedString]) -> tuple[float, int]:
    translator = FakeTranslator()
    targets = DEFAULT_LOCALES
    t0 = time.perf_counter()
    count = 0
    for e in extracted:
        for locale in targets:
            translator.translate(e.key, e.default_value, locale)
            count += 1
    return time.perf_counter() - t0, count


def measure_validation(
    extracted: list[ExtractedString],
    translations: list[Translation],
) -> dict[str, float]:
    from collections.abc import Callable

    from .validators import (
        validate_icu,
        validate_length,
        validate_plural_coverage,
        validate_unicode,
    )

    src_by_key = {e.key: e.default_value for e in extracted}

    def _rate(fn: Callable[[Translation, str], object]) -> float:
        t0 = time.perf_counter()
        for t in translations:
            fn(t, src_by_key.get(t.key, ""))
        elapsed = time.perf_counter() - t0
        return len(translations) / max(elapsed, 1e-9)

    pairs: list[tuple[str, Callable[[Translation, str], object]]] = [
        ("icu", lambda t, _src: validate_icu(t.key, t.locale, t.translated_text)),
        ("plural", lambda t, src: validate_plural_coverage(t.key, t.locale, src, t.translated_text)),
        ("unicode", lambda t, _src: validate_unicode(t.key, t.locale, t.translated_text)),
        ("length", lambda t, src: validate_length(t.key, t.locale, src, t.translated_text)),
    ]
    results: dict[str, float] = {label: _rate(fn) for label, fn in pairs}
    t0 = time.perf_counter()
    validate_all(extracted, translations)
    results["full_pipeline_seconds"] = time.perf_counter() - t0
    return results


def run_bench(n: int, files: int) -> BenchResult:
    workdir = Path(tempfile.mkdtemp(prefix="localebridge-bench-"))
    src = workdir / "src"
    try:
        synthesize_react_app(src, n=n, files=files)
        ext_seconds, files_scanned, n_extracted, peak_mb = measure_extraction(src)
        # Build the in-memory equivalent so we can measure translation and validation
        extracted = [
            ExtractedString(
                key=f"k.{i}",
                default_value=f"Hello {i}",
                source_file=f"f{i % files}.tsx",
                line=1 + (i % 50),
                context="t-call",
            )
            for i in range(n_extracted)
        ]
        translator = FakeTranslator()
        translations = [
            Translation(
                key=e.key,
                locale=locale,
                source_text=e.default_value,
                translated_text=translator.translate(e.key, e.default_value, locale),
                status="approved",
            )
            for e in extracted
            for locale in DEFAULT_LOCALES
        ]
        t_seconds, t_count = measure_translation(extracted)
        v_results = measure_validation(extracted, translations)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return BenchResult(
        n=n_extracted,
        files=files_scanned,
        extraction_seconds=ext_seconds,
        extraction_files_per_sec=files_scanned / max(ext_seconds, 1e-9),
        extraction_strings_per_sec=n_extracted / max(ext_seconds, 1e-9),
        extraction_peak_mb=peak_mb,
        translation_seconds=t_seconds,
        translation_per_sec=t_count / max(t_seconds, 1e-9),
        icu_validations_per_sec=v_results["icu"],
        plural_validations_per_sec=v_results["plural"],
        unicode_validations_per_sec=v_results["unicode"],
        length_validations_per_sec=v_results["length"],
    )


def regress(threshold: float, n: int, files: int) -> int:
    current = run_bench(n=n, files=files)
    if not BASELINE_PATH.exists():
        BASELINE_PATH.write_text(json.dumps(asdict(current), indent=2) + "\n", encoding="utf-8")
        print(f"bench-regress: no baseline; wrote {BASELINE_PATH}")
        print(json.dumps(asdict(current), indent=2))
        return 0
    baseline_raw = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    print("=== current ===")
    print(json.dumps(asdict(current), indent=2))
    print("=== baseline ===")
    print(json.dumps(baseline_raw, indent=2))
    failed: list[str] = []
    # For throughput metrics, going DOWN by more than threshold% is a regression.
    throughput_keys = [
        "extraction_files_per_sec",
        "extraction_strings_per_sec",
        "translation_per_sec",
        "icu_validations_per_sec",
        "plural_validations_per_sec",
        "unicode_validations_per_sec",
        "length_validations_per_sec",
    ]
    cur = asdict(current)
    for k in throughput_keys:
        base = baseline_raw.get(k, 0.0)
        if base <= 0:
            continue
        drift = (cur[k] - base) / base
        if drift < -threshold:
            failed.append(f"{k}: {cur[k]:.1f} vs baseline {base:.1f}  ({drift * 100:.1f}%)")
    if failed:
        print("\nbench-regress: regressions:")
        for f in failed:
            print("  " + f)
        return 1
    print(f"\nbench-regress: OK (within {threshold * 100:.0f}% threshold)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="LocaleBridge bench harness")
    p.add_argument("--n", type=int, default=10000, help="number of synthesized strings")
    p.add_argument("--files", type=int, default=200, help="number of synthesized files")
    p.add_argument("--regress", action="store_true", help="compare to baseline and exit nonzero on drift")
    p.add_argument("--threshold", type=float, default=0.30, help="regression threshold (fraction)")
    args = p.parse_args()
    if args.regress:
        return regress(threshold=args.threshold, n=args.n, files=args.files)
    result = run_bench(n=args.n, files=args.files)
    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
