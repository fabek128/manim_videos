"""Codifica una secuencia de frames BGR a MP4 con el `ffmpeg` del sistema
(mismo binario que ya invoca `build.py::combine_videos`; no se agrega un
binding Python de ffmpeg). Los frames se pipean por stdin: no se
materializan miles de PNG intermedios en disco."""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Iterable

import numpy as np

from .errors import EncodeError


def encode_frames_to_mp4(
    frames: Iterable[np.ndarray],
    output_path: Path,
    fps: int,
    size: tuple[int, int],
) -> Path:
    """Codifica `frames` (BGR, `size = (width, height)`) a H.264/yuv420p en
    `output_path`. Lanza `EncodeError` si ffmpeg no está instalado, si algún
    frame no calza con `size`, si ffmpeg termina con código de error, o si
    no se generó ningún frame."""
    width, height = size
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}", "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path),
    ]
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as exc:
        raise EncodeError("ffmpeg no encontrado. Instalá con: brew install ffmpeg") from exc

    # Drena stderr en un thread aparte: si no se lee concurrentemente, un
    # ffmpeg que escriba suficiente a stderr mientras nosotros escribimos a
    # stdin puede deadlockear ambos procesos (pipe lleno de los dos lados).
    stderr_chunks: list[bytes] = []

    def _drain_stderr() -> None:
        assert proc.stderr is not None
        for chunk in iter(lambda: proc.stderr.read(4096), b""):
            stderr_chunks.append(chunk)

    drain_thread = threading.Thread(target=_drain_stderr, daemon=True)
    drain_thread.start()

    frame_count = 0
    try:
        assert proc.stdin is not None
        for frame in frames:
            if frame.shape[1] != width or frame.shape[0] != height:
                raise EncodeError(
                    f"Frame #{frame_count} con tamaño {frame.shape[1]}x{frame.shape[0]}, "
                    f"esperado {width}x{height}"
                )
            proc.stdin.write(frame.tobytes())
            frame_count += 1
    except BrokenPipeError:
        pass  # ffmpeg murió antes de tiempo; returncode/stderr de abajo explican por qué
    finally:
        if proc.stdin is not None and not proc.stdin.closed:
            try:
                proc.stdin.close()
            except BrokenPipeError:
                pass

    returncode = proc.wait()
    drain_thread.join(timeout=5)
    stderr_text = b"".join(stderr_chunks).decode("utf-8", errors="replace").strip()
    if returncode != 0:
        raise EncodeError(f"ffmpeg falló (exit {returncode}): {stderr_text}")
    if frame_count == 0:
        raise EncodeError("No se generó ningún frame; ffmpeg no puede producir un MP4 vacío")
    return output_path
