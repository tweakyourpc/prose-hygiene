from __future__ import annotations

from zipfile import ZipFile

from prose_hygiene.engine import (
    clean_directory_to_output,
    clean_file_to_output,
    clean_zip_to_output,
    should_ignore_file,
)


def test_clean_file_to_output_rewrites_and_reports(tmp_path):
    input_path = tmp_path / "README.md"
    output_path = tmp_path / "clean" / "README.md"
    input_path.write_text("It works — but only after restart.\n", encoding="utf-8")

    report = clean_file_to_output(input_path, output_path)

    assert output_path.read_text(encoding="utf-8") == "It works, but only after restart.\n"
    assert report.kind == "file"
    assert report.summary["files"] == 1
    assert report.summary["fixed"] == 1
    assert report.summary["matches"] == 1
    assert report.strategies == {"comma": 1}
    assert report.files[0].relative_path == "README.md"


def test_clean_directory_to_output_handles_fixed_ignored_and_copied_files(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    docs_dir = input_dir / "docs"
    assets_dir = input_dir / "assets"
    docs_dir.mkdir(parents=True)
    assets_dir.mkdir(parents=True)

    (docs_dir / "fix.md").write_text("Step 1 — Set Up the Google Sheet\n", encoding="utf-8")
    (docs_dir / "skip.md").write_text(
        "<!-- prose-hygiene: ignore-file -->\nKeep — this line unchanged.\n",
        encoding="utf-8",
    )
    (assets_dir / "logo.bin").write_bytes(b"\x00\x01\x02")

    report = clean_directory_to_output(input_dir, output_dir)

    assert (output_dir / "docs" / "fix.md").read_text(encoding="utf-8") == (
        "Step 1: Set Up the Google Sheet\n"
    )
    assert (output_dir / "docs" / "skip.md").read_text(encoding="utf-8") == (
        "<!-- prose-hygiene: ignore-file -->\nKeep — this line unchanged.\n"
    )
    assert (output_dir / "assets" / "logo.bin").read_bytes() == b"\x00\x01\x02"
    assert report.summary["files"] == 3
    assert report.summary["fixed"] == 1
    assert report.summary["ignored"] == 1
    assert report.summary["copied"] == 1


def test_clean_zip_to_output_rewrites_zip_entries(tmp_path):
    input_zip = tmp_path / "input.zip"
    output_zip = tmp_path / "output.zip"

    with ZipFile(input_zip, "w") as archive:
        archive.writestr("docs/readme.md", "Inventory tab — paste from SolarWinds\n")
        archive.writestr("notes.txt", "Alpha — but beta.\n")
        archive.writestr("image.bin", b"\x03\x04")

    report = clean_zip_to_output(input_zip, output_zip)

    with ZipFile(output_zip) as archive:
        assert archive.read("docs/readme.md").decode("utf-8") == (
            "Inventory tab: paste from SolarWinds\n"
        )
        assert archive.read("notes.txt").decode("utf-8") == "Alpha, but beta.\n"
        assert archive.read("image.bin") == b"\x03\x04"

    assert report.kind == "zip"
    assert report.summary["files"] == 3
    assert report.summary["fixed"] == 2
    assert report.summary["matches"] == 2
    assert report.strategies == {"colon": 1, "comma": 1}


def test_should_ignore_file_supports_legacy_marker():
    assert should_ignore_file("em-dash-scrubber: ignore-file\nBody — stays.\n")
