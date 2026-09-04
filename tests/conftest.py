"""Gemeinsame Testhilfen: isolierte portable Wurzel je Test."""

from __future__ import annotations

import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pkc.paths import Paths  # noqa: E402


@pytest.fixture
def portable_root(tmp_path: Path, monkeypatch) -> Paths:
    """Eine frische portable Wurzel - simuliert eine leere SSD."""
    monkeypatch.setenv("KIM_ROOT", str(tmp_path))
    paths = Paths(tmp_path)
    paths.ensure_runtime_dirs()
    paths.write_marker()
    return paths


class _Handler(BaseHTTPRequestHandler):
    """Testserver mit ETag-/If-None-Match-Unterstuetzung."""

    documents: dict[str, tuple[bytes, str, str]] = {}
    hits: dict[str, int] = {}

    def log_message(self, *args) -> None:  # Testausgabe ruhig halten
        pass

    def _serve(self, body: bool) -> None:
        entry = self.documents.get(self.path)
        self.hits[self.path] = self.hits.get(self.path, 0) + 1
        if entry is None:
            self.send_response(404)
            self.end_headers()
            return
        payload, content_type, etag = entry
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("ETag", etag)
        self.end_headers()
        if body:
            self.wfile.write(payload)

    def do_GET(self) -> None:
        self._serve(True)

    def do_HEAD(self) -> None:
        self._serve(False)


@pytest.fixture
def http_server():
    """Lokaler HTTP-Server; ersetzt im Test die amtlichen Quellen."""
    _Handler.documents = {}
    _Handler.hits = {}
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    class Control:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        handler = _Handler

        def add(self, path: str, payload: bytes, content_type: str = "text/html", etag: str = '"v1"'):
            _Handler.documents[path] = (payload, content_type, etag)
            return f"{self.base}{path}"

        def hits(self, path: str) -> int:
            return _Handler.hits.get(path, 0)

    try:
        yield Control()
    finally:
        server.shutdown()
        server.server_close()
