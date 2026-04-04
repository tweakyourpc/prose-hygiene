from __future__ import annotations

from pathlib import PurePosixPath

import pytest

from prose_hygiene.web import (
    MAX_REQUEST_BYTES,
    ScrubberHTTPServer,
    _normalize_upload_path,
    build_whoami,
    write_folder_upload,
)


def test_normalize_upload_path_accepts_regular_relative_path():
    assert _normalize_upload_path("folder/docs/readme.md") == PurePosixPath("folder/docs/readme.md")


@pytest.mark.parametrize("relative_path", ["../secret.txt", "folder/../../secret.txt", "/tmp/x"])
def test_normalize_upload_path_rejects_traversal_and_absolute_paths(relative_path):
    with pytest.raises(ValueError):
        _normalize_upload_path(relative_path)


def test_write_folder_upload_preserves_root_and_writes_files(tmp_path):
    root_name = write_folder_upload(
        tmp_path,
        ["docs/readme.md", "docs/guide/notes.txt"],
        [b"alpha", b"beta"],
    )

    assert root_name == "docs"
    assert (tmp_path / "docs" / "readme.md").read_bytes() == b"alpha"
    assert (tmp_path / "docs" / "guide" / "notes.txt").read_bytes() == b"beta"


def test_server_close_removes_storage_root():
    server = ScrubberHTTPServer(("127.0.0.1", 0))
    storage_root = server.storage_root

    assert storage_root.exists()
    server.server_close()
    assert not storage_root.exists()


def test_build_whoami_payload_contains_expected_metadata():
    payload = build_whoami(host="0.0.0.0", port=8123, started_at="2026-04-04T00:00:00Z")

    assert payload["service"] == "prose-hygiene-web"
    assert payload["host"] == "0.0.0.0"
    assert payload["port"] == 8123
    assert payload["startedAt"] == "2026-04-04T00:00:00Z"


def test_max_request_bytes_is_large_enough_for_local_demo():
    assert MAX_REQUEST_BYTES >= 25 * 1024 * 1024
