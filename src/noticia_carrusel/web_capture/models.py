from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

EasingName = Literal["linear", "ease_in", "ease_out", "ease_in_out"]


class VisionCheckResult(BaseModel):
    """Resultado del chequeo de visión sobre un screenshot."""

    clean: bool
    issues: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    raw_response: str | None = None


class CaptureConfig(BaseModel):
    """Configuración de una captura de pantalla vía Playwright."""

    url: str
    viewport: tuple[int, int] = (1920, 1080)
    scale: int = Field(default=2, ge=1, le=4, description="device_scale_factor")
    full_page: bool = False
    selector: str | None = None
    wait_for_selector: str | None = None
    wait_for_network_idle: bool = False
    delay_ms: int = Field(default=0, ge=0, le=60_000)
    timeout_ms: int = Field(default=30_000, ge=1_000, le=120_000)
    vision_check: bool = Field(default=True, description="Si es True, valida el screenshot con el rol de visión")
    strict_vision: bool = Field(default=False, description="Si es True, un clean==false lanza ScreenshotRejectedError")

    @field_validator("url")
    @classmethod
    def _http_or_https(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError(
                f"url debe usar http:// o https:// (recibido: {value!r}); "
                "otros esquemas (file://, javascript:, data:) no están soportados"
            )
        return value


class CameraKeyframe(BaseModel):
    """Estado de cámara en un instante `time` (segundos desde el inicio).

    `x`/`y` son coordenadas normalizadas del centro respecto de la imagen
    fuente (0.5, 0.5 = centro). `easing` describe la curva del tramo que
    **termina** en este keyframe (se ignora en el primer keyframe).
    """

    time: float = Field(ge=0.0)
    x: float = Field(default=0.5, ge=0.0, le=1.0)
    y: float = Field(default=0.5, ge=0.0, le=1.0)
    zoom: float = Field(default=1.0, ge=1.0)
    easing: EasingName = "ease_in_out"


class CameraTimeline(BaseModel):
    """Secuencia ordenada de keyframes que describe un movimiento de cámara."""

    keyframes: list[CameraKeyframe] = Field(min_length=1)

    @model_validator(mode="after")
    def _sorted_unique_times(self) -> "CameraTimeline":
        times = [k.time for k in self.keyframes]
        if times != sorted(times):
            raise ValueError("los keyframes deben estar ordenados por `time` ascendente")
        if len(set(times)) != len(times):
            raise ValueError("no puede haber dos keyframes con el mismo `time`")
        return self

    @property
    def duration(self) -> float:
        return self.keyframes[-1].time


class WebSceneConfig(BaseModel):
    """Recurso `type: "web"` de un video: captura + movimiento de cámara."""

    capture: CaptureConfig
    duration: float = Field(gt=0.0)
    fps: int = Field(default=30, ge=1, le=60)
    camera: CameraTimeline | None = None
    zoom_to: str | None = None
    padding: float = Field(default=0.15, ge=0.0, le=0.5)

    @model_validator(mode="after")
    def _camera_xor_zoom_to(self) -> "WebSceneConfig":
        if self.camera is not None and self.zoom_to is not None:
            raise ValueError("`camera` y `zoom_to` son mutuamente excluyentes")
        return self
