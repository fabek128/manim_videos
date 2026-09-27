#!/usr/bin/env python3
"""Servidor local de videos para redes2.

Sirve los videos generados por build.py con una página índice y un player
<video> en el navegador. Escucha en 0.0.0.0 para que la URL sea accesible
desde cualquier dispositivo de la red local (celular, tablet, otra máquina).

Solo expone videos (`.mp4`/`.webm`) y las páginas del índice: cualquier otro
archivo (`.env`, configs, fuentes) devuelve 404 a propósito.

Uso:
    python scripts/serve_videos.py                 # sirve en 0.0.0.0:8765
    python scripts/serve_videos.py --port 9001     # puerto custom
    python scripts/serve_videos.py --open          # abre el navegador
    SERVE_PORT=9001 python scripts/serve_videos.py # puerto vía env

build.py levanta este servidor en background con `--serve` y muestra la
URL de cada video recién renderizado.
"""

from __future__ import annotations

import argparse
import html
import os
import posixpath
import socket
import subprocess
import sys
import time
import urllib.parse
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VIDEO_EXTS = {".mp4", ".webm"}
# Verificación de aliveness para build.py: no cuenta como archivo servido.
PING_PATH = "/__ping__"
WATCH_PATH = "/watch"
VIDEO_MOUNT = "/v"

DEFAULT_PORT = int(os.environ.get("SERVE_PORT", "8300"))


def _port() -> int:
    return int(os.environ.get("SERVE_PORT", DEFAULT_PORT))


def discover_videos(root: Path = REPO_ROOT) -> list[Path]:
    """Todos los videos del repo (relativos a `root`), más nuevos primero."""
    exclude = {".git", ".venv", "__pycache__", "node_modules", "logs"}
    videos: list[Path] = []
    for candidate in root.rglob("*"):
        if candidate.is_file() and candidate.suffix.lower() in VIDEO_EXTS:
            parts = candidate.relative_to(root).parts
            if any(part in exclude for part in parts):
                continue
            videos.append(candidate.relative_to(root))
    videos.sort(key=lambda p: (root / p).stat().st_mtime, reverse=True)
    return videos


def _resolve_video(root: Path, rel: str) -> Path | None:
    """Resuelve un path relativo de video de forma segura (sin salir de root)."""
    if not rel or rel.startswith("/") or "\\" in rel:
        return None
    norm = posixpath.normpath(urllib.parse.unquote(rel))
    if norm == "." or norm.startswith("../") or norm.startswith("/"):
        return None
    path = (root / norm).resolve()
    if path.suffix.lower() not in VIDEO_EXTS:
        return None
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return None
    return path if path.is_file() else None


def lan_ip() -> str:
    """IP de la máquina en la red local (fallback 127.0.0.1)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def human_size(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} GB"


def _video_rel_mount(rel: Path) -> str:
    """URL (path-encoded) del archivo de video servido."""
    return f"{VIDEO_MOUNT}/{urllib.parse.quote(str(rel))}"


def video_url(base: str, root: Path, rel: Path) -> str:
    """URL directa del archivo mp4 (reproducible en <video src> o link)."""
    return f"{base}{_video_rel_mount(rel)}"


def watch_url(base: str, root: Path, rel: Path) -> str:
    """URL de la página con player grande para un video."""
    quoted = urllib.parse.quote(str(rel))
    return f"{base}{WATCH_PATH}?path={quoted}"


def index_html(root: Path, base_host: str) -> str:
    videos = discover_videos(root)
    latest = videos[0] if videos else None
    latest_stat = (root / latest).stat() if latest else None

    def latest_block() -> str:
        if not latest:
            return '<p class="empty">Todavía no hay videos generados. Corré '
            "<code>python build.py --serve</code> para renderizar y ver el "
            "resultado acá.</p>"
        rel = latest
        src = _video_rel_mount(rel)
        size = human_size(latest_stat.st_size)
        mtime = datetime.fromtimestamp(latest_stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        return (
            f'<video controls preload="metadata" src="{html.escape(src)}"></video>'
            f'<div class="meta">'
            f'<a href="{WATCH_PATH}?path={urllib.parse.quote(str(rel))}">{html.escape(str(rel))}</a>'
            f'<span>{size} · {mtime}</span></div>'
        )

    rows = []
    for rel in videos:
        stat = (root / rel).stat()
        size = human_size(stat.st_size)
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        watch = f"{WATCH_PATH}?path={urllib.parse.quote(str(rel))}"
        rows.append(
            "<tr>"
            f'<td class="name"><a href="{html.escape(watch)}">{html.escape(str(rel))}</a></td>'
            f"<td>{size}</td><td>{mtime}</td>"
            f'<td><a href="{_video_rel_mount(rel)}">archivo</a></td>'
            "</tr>"
        )
    rows_html = "".join(rows)

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Videos · redes2</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin: 0; font-family: system-ui, -apple-system, sans-serif; background: #0d1117; color: #e6edf3; }}
  main {{ max-width: 960px; margin: 0 auto; padding: 2rem 1rem; }}
  h1 {{ font-size: 1.4rem; margin: 0 0 .25rem; }}
  h1 code {{ color: #ccff00; font-weight: 600; }}
  p.sub {{ color: #8b949e; margin: 0 0 1.5rem; }}
  .latest {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 1rem; margin-bottom: 2rem; }}
  .latest h2 {{ margin: 0 0 .75rem; font-size: .85rem; text-transform: uppercase; letter-spacing: .08em; color: #8b949e; }}
  video {{ width: 100%; max-height: 70vh; background: #000; border-radius: 8px; }}
  .meta {{ display: flex; justify-content: space-between; gap: 1rem; margin-top: .5rem; font-size: .85rem; color: #8b949e; }}
  .meta a {{ color: #ccff00; text-decoration: none; word-break: break-all; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .85rem; }}
  th, td {{ text-align: left; padding: .5rem .25rem; border-bottom: 1px solid #21262d; }}
  th {{ color: #8b949e; font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; }}
  td.name a {{ color: #e6edf3; text-decoration: none; }}
  td.name a:hover {{ color: #ccff00; }}
  td a {{ color: #8b949e; }}
  .empty {{ color: #8b949e; }}
  p.hint {{ color: #5d6672; font-size: .8rem; margin-top: 2rem; }}
</style>
</head>
<body>
<main>
  <h1>Videos · <code>redes2</code></h1>
  <p class="sub">Servidor local — {html.escape(base_host)}</p>
  <section class="latest">
    <h2>Último generado</h2>
    {latest_block()}
  </section>
  <table>
    <thead><tr><th>Video</th><th>Tamaño</th><th>Generado</th><th></th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  <p class="hint">Los videos se regeneran con <code>python build.py --serve</code>.
  Esta página queda siempre disponible mientras el servidor esté corriendo.</p>
</main>
</body>
</html>
"""


def watch_html(root: Path, rel: Path) -> str:
    src = _video_rel_mount(rel)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(str(rel))} · redes2</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin: 0; font-family: system-ui, -apple-system, sans-serif; background: #0d1117; color: #e6edf3; }}
  main {{ max-width: 960px; margin: 0 auto; padding: 2rem 1rem; }}
  video {{ width: 100%; max-height: 80vh; background: #000; border-radius: 8px; }}
  .nav {{ display: flex; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; font-size: .85rem; }}
  .nav a {{ color: #ccff00; text-decoration: none; }}
  .meta {{ color: #8b949e; font-size: .85rem; margin-top: .5rem; word-break: break-all; }}
</style>
</head>
<body>
<main>
  <div class="nav"><a href="/">← Todos los videos</a><a href="{html.escape(src)}">archivo directo</a></div>
  <video controls preload="metadata" src="{html.escape(src)}"></video>
  <p class="meta">{html.escape(str(rel))}</p>
</main>
</body>
</html>
"""


def make_handler(root: Path):
    """Handler HTTP con el repo `root` como base de videos."""

    class Handler(BaseHTTPRequestHandler):
        server_version = "redes2-serve/1.0"
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: object) -> None:  # silencioso
            pass

        # --- helpers -----------------------------------------------------

        def _send_bytes(self, status: int, body: bytes, ctype: str, cache: str = "no-store") -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _serve_video(self, rel: str) -> None:
            path = _resolve_video(root, rel)
            if path is None:
                self._send_bytes(404, b"not found", "text/plain; charset=utf-8")
                return
            size = path.stat().st_size
            start, end = 0, size - 1
            status = 200
            range_header = self.headers.get("Range")
            if range_header:
                m = None
                try:
                    import re

                    m = re.match(r"bytes=(\d*)-(\d*)", range_header.strip())
                except Exception:
                    m = None
                if m and (m.group(1) or m.group(2)):
                    if m.group(1):
                        start = int(m.group(1))
                        end = int(m.group(2)) if m.group(2) else size - 1
                    else:  # suffix: bytes=-N → últimos N bytes
                        end = size - 1
                        start = max(0, size - int(m.group(2)))
                    if start >= size:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{size}")
                        self.end_headers()
                        return
                    end = min(end, size - 1)
                    status = 206
            length = end - start + 1
            self.send_response(status)
            self.send_header(
                "Content-Type",
                "video/mp4" if path.suffix.lower() == ".mp4" else "video/webm",
            )
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(length))
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            if self.command != "HEAD":
                with path.open("rb") as fh:
                    fh.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = fh.read(min(65536, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)

        # --- routes ------------------------------------------------------

        def do_HEAD(self) -> None:  # noqa: N802 (API BaseHTTPRequestHandler)
            self.do_GET()

        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlsplit(self.path)
            path = parsed.path
            if path == PING_PATH:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", "2")
                self.send_header("X-Redes2-Serve", "1")
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(b"ok")
                return
            if path in ("/", "/index.html"):
                body = index_html(root, lan_ip()).encode("utf-8")
                self._send_bytes(200, body, "text/html; charset=utf-8")
                return
            if path == WATCH_PATH:
                rel = urllib.parse.parse_qs(parsed.query).get("path", [""])[0]
                resolve = _resolve_video(root, rel)
                if resolve is None:
                    self._send_bytes(404, b"video not found", "text/plain; charset=utf-8")
                    return
                body = watch_html(root, resolve.relative_to(root)).encode("utf-8")
                self._send_bytes(200, body, "text/html; charset=utf-8")
                return
            if path.startswith(VIDEO_MOUNT + "/"):
                self._serve_video(path[len(VIDEO_MOUNT) + 1 :])
                return
            self._send_bytes(404, b"not found", "text/plain; charset=utf-8")

    return Handler


def _ping(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    """True si en `port` responde NUESTRO servidor (verifica /__ping__ + header)."""
    import urllib.request

    url = f"http://{host}:{port}{PING_PATH}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.headers.get("X-Redes2-Serve") == "1" and resp.read() == b"ok"
    except Exception:
        return False


def ensure_server(port: int | None = None, root: Path = REPO_ROOT) -> str:
    """Garantiza el servidor corriendo (lo levanta en background si no responde).

    Devuelve la base URL accesible desde la red local (http://<lan-ip>:<port>).
    """
    port = port or _port()
    if not _ping(port):
        log_dir = root / "logs"
        log_dir.mkdir(exist_ok=True)
        log = open(log_dir / "serve_videos.log", "ab")
        script = Path(__file__).resolve()
        subprocess.Popen(
            [sys.executable, str(script), "--port", str(port)],
            cwd=str(root),
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if _ping(port):
                break
            time.sleep(0.2)
        else:
            tail = log_dir / "serve_videos.log"
            print(f"⚠ No se pudo levantar el servidor de videos. Log: {tail}")
    return f"http://{lan_ip()}:{port}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sirve los videos de redes2 con página web local (0.0.0.0)."
    )
    parser.add_argument("--host", default="0.0.0.0", help="Interface de escucha (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=_port(), help=f"Puerto (default: {_port()})")
    parser.add_argument("--open", action="store_true", help="Abrir el navegador con el índice")
    args = parser.parse_args()

    index_url = f"http://{lan_ip()}:{args.port}/"
    local_url = f"http://127.0.0.1:{args.port}/"
    print(f"🌐 Servidor de videos de redes2")
    print(f"   Red local: {index_url}")
    print(f"   Local:     {local_url}")
    print(f"   Ctrl+C para detener.")

    server = ThreadingHTTPServer((args.host, args.port), make_handler(REPO_ROOT))
    if args.open:
        webbrowser.open(index_url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())