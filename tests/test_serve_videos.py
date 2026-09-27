"""Tests del servidor local de videos (scripts/serve_videos.py).

Cubren el contrato observable:
- el índice lista los videos y no expone .env;
- los videos se sirven con soporte Range (206) para seek en el navegador;
- paths maliciosos (..) y archivos no-video devuelven 404;
- watchdog /__ping__ responde para que build.py detecte el proceso.
"""

from __future__ import annotations

import http.client
import threading
from pathlib import Path

import pytest

from scripts.serve_videos import VIDEO_MOUNT, make_handler, watch_url

from http.server import ThreadingHTTPServer


@pytest.fixture()
def server(tmp_path: Path):
    """Servidor real en 127.0.0.1:<puerto libre> sirviendo tmp_path."""
    video = tmp_path / "media" / "videos" / "demo.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"A" * 1000)
    (tmp_path / ".env").write_text("SECRET=1\n")

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(tmp_path))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    try:
        yield f"127.0.0.1:{port}", video
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def _request(hostport: str, path: str, headers: dict | None = None):
    conn = http.client.HTTPConnection(hostport, timeout=5)
    conn.request("GET", path, headers=headers or {})
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp, body


def test_index_lists_videos_and_hides_env(server):
    hostport, _ = server
    resp, body = _request(hostport, "/")
    assert resp.status == 200
    assert "demo.mp4" in body.decode("utf-8")
    assert b"SECRET" not in body


def test_ping_ok(server):
    hostport, _ = server
    resp, body = _request(hostport, "/__ping__")
    assert resp.status == 200
    assert body == b"ok"


def test_video_served_full_200(server):
    hostport, video = server
    resp, body = _request(hostport, f"{VIDEO_MOUNT}/media/videos/demo.mp4")
    assert resp.status == 200
    assert len(body) == video.stat().st_size
    assert resp.getheader("Accept-Ranges") == "bytes"


def test_video_range_returns_206(server):
    hostport, video = server
    resp, body = _request(
        hostport,
        f"{VIDEO_MOUNT}/media/videos/demo.mp4",
        {"Range": "bytes=0-9"},
    )
    assert resp.status == 206
    assert body == b"A" * 10
    assert resp.getheader("Content-Range") == "bytes 0-9/1000"
    assert resp.getheader("Content-Length") == "10"


def test_video_suffix_range(server):
    hostport, _ = server
    resp, body = _request(
        hostport,
        f"{VIDEO_MOUNT}/media/videos/demo.mp4",
        {"Range": "bytes=-5"},
    )
    assert resp.status == 206
    assert body == b"A" * 5
    assert resp.getheader("Content-Range") == "bytes 995-999/1000"


def test_watch_page_serves_player(server):
    hostport, _ = server
    resp, body = _request(hostport, f"/watch?path=media%2Fvideos%2Fdemo.mp4")
    assert resp.status == 200
    assert "<video" in body.decode("utf-8")
    assert "demo.mp4" in body.decode("utf-8")


def test_env_file_not_served(server):
    hostport, _ = server
    resp, _ = _request(hostport, "/.env")
    assert resp.status == 404
    resp, _ = _request(hostport, f"{VIDEO_MOUNT}/.env")
    assert resp.status == 404


def test_path_traversal_blocked(server):
    hostport, _ = server
    resp, _ = _request(hostport, f"{VIDEO_MOUNT}/../.env")
    assert resp.status == 404
    resp, _ = _request(hostport, f"{VIDEO_MOUNT}/%2e%2e%2f.env")
    assert resp.status == 404


def test_non_video_files_not_served(server):
    hostport, _ = server
    resp, _ = _request(hostport, f"{VIDEO_MOUNT}/videos/escena.txt")
    assert resp.status == 404


def test_video_url_builders_are_consistent(tmp_path: Path):
    from scripts.serve_videos import video_url, watch_url

    rel = Path("media/videos/demo.mp4")
    base = "http://192.168.1.17:8765"
    assert video_url(base, tmp_path, rel) == f"{base}{VIDEO_MOUNT}/media/videos/demo.mp4"
    assert str(rel) in watch_url(base, tmp_path, rel)
    assert watch_url(base, tmp_path, rel).startswith(f"{base}/watch?path=")