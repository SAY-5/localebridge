"""CLI entrypoint for `localebridge-run`."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .pipeline import DEFAULT_LOCALES, run


@click.command(help="Run extraction-output -> translation -> validation -> locale-write pipeline.")
@click.option("--input", "input_path", required=True, help="Path to extractor output JSON.")
@click.option("--locales", "out_dir", required=True, help="Directory to write <lang>.json files.")
@click.option(
    "--targets",
    default=",".join(DEFAULT_LOCALES),
    help="Comma-separated target locales.",
)
def main(input_path: str, out_dir: str, targets: str) -> None:
    target_tuple = tuple(t.strip() for t in targets.split(",") if t.strip())
    report, counts = run(input_path, out_dir, targets=target_tuple)
    for locale, n in counts.items():
        click.echo(f"localebridge: wrote {n} keys -> {Path(out_dir) / f'{locale}.json'}")
    errors = [i for i in report.issues if i.severity == "error"]
    warnings = [i for i in report.issues if i.severity == "warning"]
    click.echo(f"localebridge: {len(errors)} errors, {len(warnings)} warnings")
    if errors:
        for e in errors:
            click.echo(f"  ERROR {e.code} {e.locale}/{e.key}: {e.message}", err=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
