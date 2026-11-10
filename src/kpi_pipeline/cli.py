"""Command-line entry point: ``python -m kpi_pipeline.cli``."""

from __future__ import annotations

import argparse
from pathlib import Path

from .clean import clean_samples
from .config import PROCESSED_DIR, RAW_DIR
from .export import write_outputs
from .ingest import load_raw_logs


def _parse_formats(value: str) -> tuple[str, ...]:
    formats = tuple(part.strip().lower() for part in value.split(",") if part.strip())
    if not formats:
        raise argparse.ArgumentTypeError("At least one output format is required")
    return formats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kpi-pipeline",
        description="Clean raw 5G NR cell logs and export a Power BI-ready star schema.",
    )
    parser.add_argument("--raw-dir", default=str(RAW_DIR), help="Folder containing raw CSV logs")
    parser.add_argument("--pattern", default="*.csv", help="Glob pattern for raw log files")
    parser.add_argument(
        "--out-dir", default=str(PROCESSED_DIR), help="Folder for processed outputs"
    )
    parser.add_argument(
        "--format",
        default="csv",
        type=_parse_formats,
        help="Comma-separated output formats: csv, parquet",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    raw = load_raw_logs(Path(args.raw_dir), pattern=args.pattern)
    if raw.empty:
        print(f"No raw logs found in {args.raw_dir!r} matching {args.pattern!r}.")
        return 1

    cleaned = clean_samples(raw)
    if cleaned.empty:
        print("Every raw record was rejected during cleaning. Check the input schema.")
        return 1

    outputs = write_outputs(cleaned, args.out_dir, formats=args.format)

    print(f"Loaded {len(raw):,} raw samples -> kept {len(cleaned):,} after cleaning.")
    print(f"Wrote {len(outputs)} tables to {Path(args.out_dir).resolve()}:")
    for name, paths in outputs.items():
        print(f"  - {name}: {', '.join(p.name for p in paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
