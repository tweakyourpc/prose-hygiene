"""Artifact cleaning engine for prose-hygiene."""

from __future__ import annotations

import os
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .style import rewrite_document_text


DOC_EXTENSIONS = frozenset(
    {
        ".json",
        ".md",
        ".mdx",
        ".rst",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
)

SKIP_DIRS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".next",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "venv",
    }
)

IGNORE_FILE_MARKER = "prose-hygiene: ignore-file"
LEGACY_IGNORE_FILE_MARKER = "em-dash-scrubber: ignore-file"
IGNORE_FILE_MARKERS = frozenset(
    {
        IGNORE_FILE_MARKER,
        LEGACY_IGNORE_FILE_MARKER,
        f"<!-- {IGNORE_FILE_MARKER} -->",
        f"<!-- {LEGACY_IGNORE_FILE_MARKER} -->",
    }
)


@dataclass(frozen=True)
class EngineOptions:
    """Options for reusable artifact cleaning."""

    extensions: frozenset[str] = DOC_EXTENSIONS
    skip_dirs: frozenset[str] = SKIP_DIRS
    normalize_heading_commas: bool = False

    def is_target(self, path: PurePosixPath | Path) -> bool:
        return path.suffix.lower() in self.extensions


@dataclass(frozen=True)
class ArtifactResult:
    """Result for one output artifact."""

    relative_path: str
    status: str
    scanned: bool
    count: int = 0
    strategies: dict[str, int] = field(default_factory=dict)
    note: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "relative_path": self.relative_path,
            "status": self.status,
            "scanned": self.scanned,
        }
        if self.count:
            payload["count"] = self.count
        if self.strategies:
            payload["strategies"] = self.strategies
        if self.note:
            payload["note"] = self.note
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True)
class BundleReport:
    """Summary of a cleaning run."""

    kind: str
    input_path: str
    output_path: str
    summary: dict[str, int]
    strategies: dict[str, int]
    files: list[ArtifactResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "summary": self.summary,
            "strategies": self.strategies,
            "files": [item.to_dict() for item in self.files],
        }


def should_ignore_file(text: str) -> bool:
    visible_lines = [line.strip() for line in text.splitlines() if line.strip()]
    return any(line in IGNORE_FILE_MARKERS for line in visible_lines[:15])


def _new_summary() -> dict[str, int]:
    return {
        "files": 0,
        "scanned": 0,
        "fixed": 0,
        "ignored": 0,
        "clean": 0,
        "copied": 0,
        "errors": 0,
        "matches": 0,
    }


def _update_summary(summary: dict[str, int], result: ArtifactResult) -> None:
    summary["files"] += 1
    if result.scanned:
        summary["scanned"] += 1

    if result.status == "fixed":
        summary["fixed"] += 1
        summary["matches"] += result.count
    elif result.status == "ignored":
        summary["ignored"] += 1
    elif result.status == "clean":
        summary["clean"] += 1
    elif result.status == "copied":
        summary["copied"] += 1
    elif result.status == "error":
        summary["errors"] += 1


def _validate_output_path(input_path: Path, output_path: Path) -> None:
    if input_path.resolve() == output_path.resolve():
        raise ValueError("input and output paths must be different")


def _scan_allowed(relative_path: PurePosixPath, options: EngineOptions) -> bool:
    return not any(part in options.skip_dirs for part in relative_path.parts[:-1])


def _process_bytes(
    relative_path: PurePosixPath,
    raw: bytes,
    options: EngineOptions,
    scan_allowed: bool,
) -> tuple[bytes, ArtifactResult]:
    if not options.is_target(relative_path):
        return raw, ArtifactResult(
            relative_path=str(relative_path),
            status="copied",
            scanned=False,
            note="non-target",
        )

    if not scan_allowed:
        return raw, ArtifactResult(
            relative_path=str(relative_path),
            status="copied",
            scanned=False,
            note="skip-dir",
        )

    text = raw.decode("utf-8", errors="ignore")
    if should_ignore_file(text):
        return raw, ArtifactResult(
            relative_path=str(relative_path),
            status="ignored",
            scanned=True,
        )

    rewritten = rewrite_document_text(text, normalize_heading_commas=options.normalize_heading_commas)
    if rewritten.count == 0:
        return raw, ArtifactResult(
            relative_path=str(relative_path),
            status="clean",
            scanned=True,
        )

    return rewritten.text.encode("utf-8"), ArtifactResult(
        relative_path=str(relative_path),
        status="fixed",
        scanned=True,
        count=rewritten.count,
        strategies=rewritten.strategies,
    )


def _finalize_report(
    kind: str,
    input_path: Path,
    output_path: Path,
    summary: dict[str, int],
    strategy_counter: Counter[str],
    files: list[ArtifactResult],
) -> BundleReport:
    return BundleReport(
        kind=kind,
        input_path=str(input_path.resolve()),
        output_path=str(output_path.resolve()),
        summary=summary,
        strategies=dict(strategy_counter),
        files=files,
    )


def clean_file_to_output(
    input_path: Path,
    output_path: Path,
    options: EngineOptions | None = None,
) -> BundleReport:
    """Clean one file into another file."""
    options = options or EngineOptions()
    _validate_output_path(input_path, output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = _new_summary()
    strategies: Counter[str] = Counter()
    files: list[ArtifactResult] = []
    relative_path = PurePosixPath(input_path.name)

    try:
        raw = input_path.read_bytes()
        output_bytes, result = _process_bytes(relative_path, raw, options, scan_allowed=True)
    except OSError as exc:
        result = ArtifactResult(
            relative_path=str(relative_path),
            status="error",
            scanned=False,
            error=str(exc),
        )
    else:
        try:
            output_path.write_bytes(output_bytes)
        except OSError as exc:
            result = ArtifactResult(
                relative_path=str(relative_path),
                status="error",
                scanned=result.scanned,
                error=str(exc),
            )

    files.append(result)
    _update_summary(summary, result)
    strategies.update(result.strategies)
    return _finalize_report("file", input_path, output_path, summary, strategies, files)


def clean_directory_to_output(
    input_dir: Path,
    output_dir: Path,
    options: EngineOptions | None = None,
) -> BundleReport:
    """Clean one directory tree into another directory tree."""
    options = options or EngineOptions()
    _validate_output_path(input_dir, output_dir)
    if output_dir.resolve().is_relative_to(input_dir.resolve()):
        raise ValueError("output directory must not be inside the input directory")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = _new_summary()
    strategies: Counter[str] = Counter()
    files: list[ArtifactResult] = []

    for dirpath, dirnames, filenames in os.walk(input_dir):
        dirnames[:] = sorted(dirnames)
        filenames = sorted(filenames)

        current_dir = Path(dirpath)
        relative_dir = current_dir.relative_to(input_dir)
        target_dir = output_dir / relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        for filename in filenames:
            source_path = current_dir / filename
            relative_path = source_path.relative_to(input_dir)
            destination_path = output_dir / relative_path
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                raw = source_path.read_bytes()
                output_bytes, result = _process_bytes(
                    PurePosixPath(relative_path.as_posix()),
                    raw,
                    options,
                    scan_allowed=_scan_allowed(PurePosixPath(relative_path.as_posix()), options),
                )
                destination_path.write_bytes(output_bytes)
            except OSError as exc:
                result = ArtifactResult(
                    relative_path=relative_path.as_posix(),
                    status="error",
                    scanned=False,
                    error=str(exc),
                )

            files.append(result)
            _update_summary(summary, result)
            strategies.update(result.strategies)

    return _finalize_report("directory", input_dir, output_dir, summary, strategies, files)


def clean_zip_to_output(
    input_zip: Path,
    output_zip: Path,
    options: EngineOptions | None = None,
) -> BundleReport:
    """Clean one zip archive into another zip archive."""
    options = options or EngineOptions()
    _validate_output_path(input_zip, output_zip)
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    summary = _new_summary()
    strategies: Counter[str] = Counter()
    files: list[ArtifactResult] = []

    with zipfile.ZipFile(input_zip) as source_archive, zipfile.ZipFile(
        output_zip,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as target_archive:
        for info in sorted(source_archive.infolist(), key=lambda item: item.filename):
            archive_path = PurePosixPath(info.filename)
            if info.is_dir():
                target_archive.writestr(info, b"")
                continue

            try:
                raw = source_archive.read(info.filename)
                output_bytes, result = _process_bytes(
                    archive_path,
                    raw,
                    options,
                    scan_allowed=_scan_allowed(archive_path, options),
                )
                target_archive.writestr(info, output_bytes)
            except OSError as exc:
                result = ArtifactResult(
                    relative_path=info.filename,
                    status="error",
                    scanned=False,
                    error=str(exc),
                )

            files.append(result)
            _update_summary(summary, result)
            strategies.update(result.strategies)

    return _finalize_report("zip", input_zip, output_zip, summary, strategies, files)


def clean_input(
    input_path: Path | str,
    output_path: Path | str,
    options: EngineOptions | None = None,
) -> BundleReport:
    """Clean a file, directory, or zip archive to an explicit output path."""
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"input path does not exist: {input_path}")

    if input_path.is_dir():
        return clean_directory_to_output(input_path, output_path, options)

    if input_path.suffix.lower() == ".zip":
        return clean_zip_to_output(input_path, output_path, options)

    return clean_file_to_output(input_path, output_path, options)
