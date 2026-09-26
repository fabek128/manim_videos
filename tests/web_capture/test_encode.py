import json
import subprocess
from pathlib import Path
from typing import Iterator

import numpy as np
import pytest

from noticia_carrusel.web_capture.encode import encode_frames_to_mp4
from noticia_carrusel.web_capture.errors import EncodeError


def _ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


requires_ffmpeg = pytest.mark.skipif(
    not _ffmpeg_available(), reason="ffmpeg/ffprobe no está instalado"
)


def _synthetic_frames(n: int, size: tuple[int, int]) -> Iterator[np.ndarray]:
    width, height = size
    for i in range(n):
        yield np.full((height, width, 3), fill_value=i % 256, dtype=np.uint8)


@requires_ffmpeg
def test_encode_produces_valid_mp4_with_expected_resolution_and_duration(tmp_path: Path):
    size = (64, 48)
    fps = 10
    n_frames = 10
    output = tmp_path / "clip.mp4"

    result = encode_frames_to_mp4(_synthetic_frames(n_frames, size), output, fps=fps, size=size)

    assert result == output
    assert output.is_file()
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height:format=duration",
            "-of", "json",
            str(output),
        ],
        capture_output=True,
        check=True,
    )
    data = json.loads(probe.stdout)
    stream = data["streams"][0]
    assert stream["width"] == size[0]
    assert stream["height"] == size[1]
    duration = float(data["format"]["duration"])
    assert duration == pytest.approx(n_frames / fps, abs=0.2)


@requires_ffmpeg
def test_encode_wrong_frame_size_raises(tmp_path: Path):
    size = (64, 48)
    bad_frame = np.zeros((10, 10, 3), dtype=np.uint8)
    with pytest.raises(EncodeError, match="tamaño"):
        encode_frames_to_mp4(iter([bad_frame]), tmp_path / "bad.mp4", fps=10, size=size)


@requires_ffmpeg
def test_encode_empty_frames_raises(tmp_path: Path):
    with pytest.raises(EncodeError, match="ningún frame"):
        encode_frames_to_mp4(iter([]), tmp_path / "empty.mp4", fps=10, size=(64, 48))


def test_encode_missing_ffmpeg_raises(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))  # PATH sin ffmpeg
    size = (64, 48)
    with pytest.raises(EncodeError, match="ffmpeg no encontrado"):
        encode_frames_to_mp4(_synthetic_frames(1, size), tmp_path / "x.mp4", fps=10, size=size)
