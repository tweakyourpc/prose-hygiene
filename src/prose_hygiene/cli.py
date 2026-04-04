#!/usr/bin/env python3
"""CLI wrapper for prose-hygiene."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import BundleReport, DOC_EXTENSIONS, EngineOptions, clean_input


def normalize_extension(value: str) -> str:
    value = value.strip().lower()
    if not value:
        raise argparse.ArgumentTypeError("extensions must not be empty")
    return value if value.startswith(".") else f".{value}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rewrite U+2014 in document-style artifacts with punctuation heuristics."
    )
    parser.add_argument("input_path", help="Input file, directory, or zip archive")
    parser.add_argument("output_path", help="Output file, directory, or zip archive")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report to stdout",
    )
    parser.add_argument(
        "--extension",
        action="append",
        type=normalize_extension,
        default=None,
        help="Override the target extension set by repeating this option",
    )
    parser.add_argument(
        "--skip-dir",
        action="append",
        default=None,
        help="Add a directory name that should be copied without scanning",
    )
    parser.add_argument(
        "--normalize-heading-commas",
        action="store_true",
        help="Also normalize heading-style single-comma lines like 'Foo, Bar' to 'Foo: Bar'",
    )
    return parser


def format_strategies(strategies: dict[str, int]) -> str:
    if not strategies:
        return "none"
    return ", ".join(f"{name}={count}" for name, count in sorted(strategies.items()))


def print_report(report: BundleReport) -> None:
    summary = report.summary
    print(f"Kind:       {report.kind}")
    print(f"Input:      {report.input_path}")
    print(f"Output:     {report.output_path}")
    print("-" * 60)
    print(f"Files:      {summary['files']}")
    print(f"Scanned:    {summary['scanned']}")
    print(f"Fixed:      {summary['fixed']}")
    print(f"Ignored:    {summary['ignored']}")
    print(f"Clean:      {summary['clean']}")
    print(f"Copied:     {summary['copied']}")
    print(f"Matches:    {summary['matches']}")
    print(f"Errors:     {summary['errors']}")
    print(f"Strategies: {format_strategies(report.strategies)}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    options = EngineOptions(
        extensions=frozenset(args.extension or DOC_EXTENSIONS),
        skip_dirs=frozenset(set(args.skip_dir or []) | set(EngineOptions().skip_dirs)),
        normalize_heading_commas=args.normalize_heading_commas,
    )

    try:
        report = clean_input(Path(args.input_path), Path(args.output_path), options)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_report(report)

    if report.summary["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
