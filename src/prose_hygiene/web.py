#!/usr/bin/env python3
"""Local web frontend for prose-hygiene.

EXPERIMENTAL: the CLI and hook workflow are the primary polished surfaces.
This module is intended for local/demo use and deserves deeper review before broader release.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default as default_policy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from . import __version__
from .engine import clean_input


SERVICE_NAME = "prose-hygiene-web"
SERVICE_VERSION = __version__
SERVICE_BUILD = "experimental"
MAX_REQUEST_BYTES = 25 * 1024 * 1024


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>prose-hygiene Web Demo</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6ede5;
      --panel: #fffaf6;
      --ink: #2c1f1a;
      --accent: #b54708;
      --accent-soft: #ffe3cf;
      --border: #e5c3ac;
      --muted: #6c4f43;
    }
    body {
      margin: 0;
      font-family: "Palatino Linotype", Georgia, serif;
      background:
        radial-gradient(circle at top left, #fffdf8 0%, #fff7f1 35%, var(--bg) 100%);
      color: var(--ink);
    }
    main {
      max-width: 960px;
      margin: 0 auto;
      padding: 36px 20px 56px;
    }
    .hero, .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 24px 48px rgba(95, 48, 24, 0.10);
    }
    .hero {
      padding: 30px;
      margin-bottom: 24px;
    }
    .hero .badge {
      display: inline-block;
      margin-bottom: 10px;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 0.9rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .hero .build {
      display: block;
      margin-top: 6px;
      margin-bottom: 16px;
      color: var(--muted);
      font-family: "Courier New", monospace;
      font-size: 0.9rem;
    }
    .grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    }
    .panel {
      padding: 22px;
    }
    h1, h2 {
      margin-top: 0;
    }
    p {
      line-height: 1.55;
    }
    form {
      display: grid;
      gap: 12px;
    }
    input[type=file] {
      width: 100%;
    }
    button {
      width: fit-content;
      background: var(--accent);
      color: #fff;
      border: 0;
      border-radius: 999px;
      padding: 10px 16px;
      font: inherit;
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.6;
      cursor: wait;
    }
    .status {
      margin-top: 24px;
      padding: 22px;
      white-space: pre-wrap;
      font-family: "Courier New", monospace;
    }
    .download {
      display: inline-block;
      margin-top: 12px;
      color: var(--accent);
      font-weight: bold;
    }
    .small {
      font-size: 0.92rem;
      color: var(--muted);
    }
    .examples {
      margin-top: 16px;
      padding: 16px;
      border-radius: 14px;
      background: #fff1e4;
      border: 1px dashed #d38b5d;
    }
    .examples h2 {
      margin-bottom: 10px;
    }
    .examples code {
      display: block;
      margin-bottom: 8px;
      white-space: pre-wrap;
      font-family: "Courier New", monospace;
      color: #8a2e0b;
    }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <span class="badge">Experimental</span>
      <span class="build">Build: experimental</span>
      <h1>prose-hygiene Web Demo</h1>
      <p>This local demo runs the same deterministic cleanup engine as the CLI. It is useful for quick trials, but the CLI and Git hook flow remain the primary release surfaces.</p>
      <p class="small">The web UI keeps the scope narrow on purpose: upload a file, folder, or zip and download the cleaned result.</p>
      <div class="examples">
        <h2>Expected Colon Examples</h2>
        <code>Step 1: Set Up the Google Sheet</code>
        <code>Inventory tab: paste from SolarWinds in this exact column order</code>
        <code>Responses Sheet: Column Reference</code>
      </div>
    </section>

    <section class="grid">
      <article class="panel">
        <h2>File Or Zip</h2>
        <form id="file-form">
          <input type="file" name="upload" required>
          <button type="submit">Clean Upload</button>
        </form>
      </article>

      <article class="panel">
        <h2>Folder</h2>
        <form id="folder-form">
          <input type="file" id="folder-input" webkitdirectory directory multiple required>
          <button type="submit">Clean Folder</button>
        </form>
        <p class="small">Folder uploads return as a cleaned zip archive.</p>
      </article>
    </section>

    <section class="panel status" id="status">Ready.</section>
    <a class="download" id="download-link" hidden>Download cleaned artifact</a>
  </main>

  <script>
    const statusEl = document.getElementById("status");
    const downloadLink = document.getElementById("download-link");

    function setStatus(text) {
      statusEl.textContent = text;
    }

    function formatStrategies(strategies) {
      const entries = Object.entries(strategies || {});
      if (!entries.length) {
        return "none";
      }
      return entries
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([name, count]) => `${name}=${count}`)
        .join(", ");
    }

    function renderReport(payload) {
      const summary = payload.report.summary;
      const lines = [
        "Kind: " + payload.report.kind,
        "Files: " + summary.files,
        "Scanned: " + summary.scanned,
        "Fixed: " + summary.fixed,
        "Ignored: " + summary.ignored,
        "Clean: " + summary.clean,
        "Copied: " + summary.copied,
        "Matches: " + summary.matches,
        "Errors: " + summary.errors,
        "Strategies: " + formatStrategies(payload.report.strategies),
      ];
      setStatus(lines.join("\\n"));
      downloadLink.href = payload.download_url;
      downloadLink.download = payload.download_name;
      downloadLink.hidden = false;
      downloadLink.textContent = "Download " + payload.download_name;
    }

    async function postFormData(formData, button) {
      downloadLink.hidden = true;
      button.disabled = true;
      setStatus("Cleaning upload...");
      try {
        const response = await fetch("/api/clean", {
          method: "POST",
          body: formData,
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "Request failed");
        }
        renderReport(payload);
      } catch (error) {
        setStatus("Error: " + error.message);
      } finally {
        button.disabled = false;
      }
    }

    document.getElementById("file-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = event.target.querySelector("button");
      const input = event.target.querySelector("input[type=file]");
      if (!input.files.length) {
        setStatus("Choose a file or zip archive first.");
        return;
      }
      const file = input.files[0];
      const formData = new FormData();
      formData.append("input_kind", file.name.toLowerCase().endsWith(".zip") ? "zip" : "file");
      formData.append("upload", file, file.name);
      await postFormData(formData, button);
    });

    document.getElementById("folder-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = event.target.querySelector("button");
      const input = document.getElementById("folder-input");
      if (!input.files.length) {
        setStatus("Choose a folder first.");
        return;
      }
      const formData = new FormData();
      formData.append("input_kind", "folder");
      for (const file of input.files) {
        formData.append("folder_files", file, file.name);
        formData.append("folder_relative_paths", file.webkitRelativePath || file.name);
      }
      await postFormData(formData, button);
    });
  </script>
</body>
</html>
"""


@dataclass(frozen=True)
class StoredArtifact:
    token: str
    path: Path
    download_name: str


@dataclass(frozen=True)
class MultipartPart:
    name: str
    data: bytes
    filename: str | None = None

    @property
    def text(self) -> str:
        return self.data.decode("utf-8", errors="ignore")


def suggest_download_name(original_name: str, force_zip: bool = False) -> str:
    base = Path(original_name).name or "artifact"
    if force_zip:
        stem = Path(base).stem or "artifact"
        return f"cleaned-{stem}.zip"
    return f"cleaned-{base}"


def _normalize_upload_path(relative_path: str) -> PurePosixPath:
    posix_path = PurePosixPath(relative_path)
    if not posix_path.parts:
        raise ValueError("folder upload contains an empty relative path")
    if posix_path.is_absolute():
        raise ValueError("folder upload paths must be relative")
    if any(part in {"", ".", ".."} for part in posix_path.parts):
        raise ValueError("folder upload paths must not contain traversal segments")
    return posix_path


def write_folder_upload(target_root: Path, relative_paths: list[str], file_payloads: list[bytes]) -> str:
    root_name = "folder"
    for relative_path, payload in zip(relative_paths, file_payloads, strict=True):
        posix_path = _normalize_upload_path(relative_path)
        if len(posix_path.parts) > 1:
            root_name = posix_path.parts[0]
        target_path = target_root / Path(*posix_path.parts)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(payload)
    return root_name


def zip_directory(source_dir: Path, output_zip: Path) -> None:
    with zipfile.ZipFile(output_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir():
                continue
            archive.write(path, arcname=path.relative_to(source_dir).as_posix())


def build_whoami(host: str, port: int, started_at: str) -> dict[str, object]:
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "build": SERVICE_BUILD,
        "pid": os.getpid(),
        "startedAt": started_at,
        "host": host,
        "port": port,
    }


def parse_multipart_form(content_type: str, body: bytes) -> dict[str, list[MultipartPart]]:
    if not content_type:
        raise ValueError("missing Content-Type header")

    message = BytesParser(policy=default_policy).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    if not message.is_multipart():
        raise ValueError("expected multipart/form-data body")

    fields: dict[str, list[MultipartPart]] = {}
    for part in message.iter_parts():
        if part.get_content_disposition() != "form-data":
            continue
        name = part.get_param("name", header="content-disposition")
        if isinstance(name, tuple):
            name = name[2]
        if not isinstance(name, str) or not name:
            continue
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            payload = b""
        item = MultipartPart(
            name=name,
            filename=part.get_filename(),
            data=payload,
        )
        fields.setdefault(name, []).append(item)
    return fields


class ScrubberHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address: tuple[str, int]) -> None:
        super().__init__(server_address, ScrubberHandler)
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.storage_root = Path(tempfile.mkdtemp(prefix="prose-hygiene-web-"))
        self.artifacts: dict[str, StoredArtifact] = {}

    def server_close(self) -> None:
        super().server_close()
        shutil.rmtree(self.storage_root, ignore_errors=True)


class ScrubberHandler(BaseHTTPRequestHandler):
    server: ScrubberHTTPServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(INDEX_HTML)
            return
        if parsed.path == "/whoami":
            raw_host = self.server.server_address[0]
            if isinstance(raw_host, (bytes, bytearray)):
                host = raw_host.decode("utf-8", errors="ignore")
            else:
                host = raw_host
            payload = build_whoami(
                host=host,
                port=self.server.server_address[1],
                started_at=self.server.started_at,
            )
            self._send_json(payload)
            return
        if parsed.path.startswith("/api/download/"):
            token = parsed.path.rsplit("/", 1)[-1]
            self._send_download(token)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/clean":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        try:
            payload = self._handle_clean_request()
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        except OSError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json(payload)

    def log_message(self, format: str, *args) -> None:
        del format, args

    def _handle_clean_request(self) -> dict[str, object]:
        content_length = self._content_length()
        form = parse_multipart_form(
            self.headers.get("Content-Type", ""),
            self.rfile.read(content_length),
        )

        input_kind = self._field_value(form, "input_kind")
        request_root = self.server.storage_root / uuid.uuid4().hex
        request_root.mkdir(parents=True, exist_ok=True)

        try:
            if input_kind in {"file", "zip"}:
                upload = self._field_list(form, "upload")[0]
                if not upload.filename:
                    raise ValueError("missing upload")
                original_name = Path(upload.filename).name
                input_path = request_root / original_name
                input_path.write_bytes(upload.data)
                output_path = request_root / suggest_download_name(
                    original_name,
                    force_zip=input_kind == "zip",
                )
                report = clean_input(input_path, output_path)
                artifact_path = output_path
                download_name = output_path.name
            elif input_kind == "folder":
                file_fields = self._field_list(form, "folder_files")
                relative_paths = [item.text for item in self._field_list(form, "folder_relative_paths")]
                if not file_fields or not relative_paths or len(file_fields) != len(relative_paths):
                    raise ValueError("folder upload is incomplete")
                input_root = request_root / "folder-input"
                output_root = request_root / "folder-output"
                input_root.mkdir(parents=True, exist_ok=True)
                payloads = [item.data for item in file_fields]
                root_name = write_folder_upload(input_root, relative_paths, payloads)
                report = clean_input(input_root, output_root)
                artifact_path = request_root / suggest_download_name(root_name, force_zip=True)
                zip_directory(output_root, artifact_path)
                download_name = artifact_path.name
            else:
                raise ValueError("unsupported input kind")
        except Exception:
            shutil.rmtree(request_root, ignore_errors=True)
            raise

        token = uuid.uuid4().hex
        self.server.artifacts[token] = StoredArtifact(
            token=token,
            path=artifact_path,
            download_name=download_name,
        )
        return {
            "download_url": f"/api/download/{token}",
            "download_name": download_name,
            "report": report.to_dict(),
        }

    def _send_download(self, token: str) -> None:
        artifact = self.server.artifacts.get(token)
        if artifact is None or not artifact.path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Download not found")
            return

        content_type = mimetypes.guess_type(artifact.download_name)[0] or "application/octet-stream"
        payload = artifact.path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Content-Disposition", f'attachment; filename="{artifact.download_name}"')
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, content: str) -> None:
        payload = content.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _field_value(form: dict[str, list[MultipartPart]], name: str) -> str:
        field = form.get(name)
        if not field:
            raise ValueError(f"missing field: {name}")
        return field[0].text

    @staticmethod
    def _field_list(form: dict[str, list[MultipartPart]], name: str) -> list[MultipartPart]:
        field = form.get(name)
        if not field:
            raise ValueError(f"missing field: {name}")
        return field

    def _content_length(self) -> int:
        raw = self.headers.get("Content-Length")
        if raw is None:
            raise ValueError("missing Content-Length header")
        try:
            content_length = int(raw)
        except ValueError as exc:
            raise ValueError("invalid Content-Length header") from exc
        if content_length < 0:
            raise ValueError("invalid Content-Length header")
        if content_length > MAX_REQUEST_BYTES:
            raise ValueError(f"request body exceeds {MAX_REQUEST_BYTES} bytes")
        return content_length


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local prose-hygiene web demo.")
    parser.add_argument("--host", default="0.0.0.0", help="Host bind address")  # nosec B104
    parser.add_argument("--port", required=True, type=int, help="Port to bind")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    server = ScrubberHTTPServer((args.host, args.port))
    print(f"Serving on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
