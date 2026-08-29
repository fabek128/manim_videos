from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def pil_to_bgr(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)


def bgr_to_pil(array: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(array, cv2.COLOR_BGR2RGB))


def detect_face_center(image: Image.Image) -> tuple[float, float] | None:
    """Devuelve el centro normalizado del rostro mayor detectado, si existe."""
    gray = cv2.cvtColor(pil_to_bgr(image), cv2.COLOR_BGR2GRAY)
    data = getattr(cv2, "data", None)
    classifier = getattr(cv2, "CascadeClassifier", None)
    cascade_dir = getattr(data, "haarcascades", None)
    if classifier is None or cascade_dir is None:
        return None
    detector = classifier(cascade_dir + "haarcascade_frontalface_default.xml")
    faces = detector.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48)
    )
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
    return ((x + w / 2) / image.width, (y + h / 2) / image.height)


def smart_crop(image: Image.Image, size: tuple[int, int], detect_subject: bool = True) -> Image.Image:
    """Recorta al aspect ratio objetivo priorizando el centro de un rostro."""
    target_w, target_h = size
    source_ratio = image.width / image.height
    target_ratio = target_w / target_h
    focus = detect_face_center(image) if detect_subject else None
    if source_ratio > target_ratio:
        crop_h = image.height
        crop_w = round(crop_h * target_ratio)
    else:
        crop_w = image.width
        crop_h = round(crop_w / target_ratio)
    center_x = (focus[0] * image.width) if focus else image.width / 2
    center_y = (focus[1] * image.height) if focus else image.height / 2
    left = max(0, min(round(center_x - crop_w / 2), image.width - crop_w))
    top = max(0, min(round(center_y - crop_h / 2), image.height - crop_h))
    return image.crop((left, top, left + crop_w, top + crop_h)).resize(size, Image.Resampling.LANCZOS)


def enhance(image: Image.Image, sharpen: float = 0.0, contrast: float = 1.0) -> Image.Image:
    """Aplica mejora moderada de contraste y enfoque con OpenCV."""
    array = pil_to_bgr(image)
    if contrast != 1.0:
        lab = cv2.cvtColor(array, cv2.COLOR_BGR2LAB)
        lightness, channel_a, channel_b = cv2.split(lab)
        lightness = cv2.convertScaleAbs(lightness, alpha=contrast, beta=0)
        array = cv2.cvtColor(cv2.merge((lightness, channel_a, channel_b)), cv2.COLOR_LAB2BGR)
    if sharpen > 0:
        blurred = cv2.GaussianBlur(array, (0, 0), 1.2)
        array = cv2.addWeighted(array, 1.0 + sharpen, blurred, -sharpen, 0)
    return bgr_to_pil(array)


def edge_density(image: Image.Image) -> float:
    """Calcula la proporción de bordes para diagnóstico de composición."""
    gray = cv2.cvtColor(pil_to_bgr(image), cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return float(np.count_nonzero(edges)) / edges.size


def load_and_prepare(path: str | Path, size: tuple[int, int], detect_subject: bool = True) -> Image.Image:
    image = Image.open(path).convert("RGB")
    return smart_crop(image, size, detect_subject)
