from __future__ import annotations

import json

from prose_hygiene.cli import main


def test_cli_json_output_smoke(tmp_path, capsys):
    input_path = tmp_path / "README.md"
    output_path = tmp_path / "README.clean.md"
    input_path.write_text("Responses Sheet, Column Reference\n", encoding="utf-8")

    exit_code = main(
        [
            str(input_path),
            str(output_path),
            "--json",
            "--normalize-heading-commas",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert output_path.read_text(encoding="utf-8") == "Responses Sheet: Column Reference\n"
    assert payload["kind"] == "file"
    assert payload["summary"]["fixed"] == 1
    assert payload["summary"]["matches"] == 1
    assert payload["strategies"] == {"colon": 1}


def test_cli_plain_output_reports_summary(tmp_path, capsys):
    input_path = tmp_path / "README.md"
    output_path = tmp_path / "README.clean.md"
    input_path.write_text("It works — but only after restart.\n", encoding="utf-8")

    exit_code = main([str(input_path), str(output_path)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Kind:       file" in captured.out
    assert "Fixed:      1" in captured.out
    assert "Matches:    1" in captured.out


def test_cli_returns_error_for_same_input_and_output(tmp_path, capsys):
    input_path = tmp_path / "README.md"
    input_path.write_text("Alpha — beta\n", encoding="utf-8")

    exit_code = main([str(input_path), str(input_path)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "input and output paths must be different" in captured.err
