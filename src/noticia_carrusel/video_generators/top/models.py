from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_relative_path(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    p = Path(value)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"{field_name} debe ser relativo y sin '..': {value!r}")
    if not value.strip():
        raise ValueError(f"{field_name} no puede estar vacío")
    return value


class TopMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(default="Tokens", min_length=1)
    value: str = Field(default="", min_length=0)

    @field_validator("label", "value", mode="before")
    @classmethod
    def _coerce_str(cls, v: object) -> str:
        return str(v) if v is not None else ""


class TopSpecRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1)
    value: str = Field(min_length=0)

    @field_validator("label", "value", mode="before")
    @classmethod
    def _coerce_str(cls, v: object) -> str:
        return str(v)

    @field_validator("label")
    @classmethod
    def _strip_label(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("label no puede estar vacío")
        return v


class TopAudio(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset: str = Field(default="sounds/intros/SunsetDrift.mp3")
    gain_db: float = Field(default=-4.0)

    @field_validator("asset")
    @classmethod
    def _asset_relative(cls, v: str) -> str:
        return _validate_relative_path(v, "audio.asset")  # type: ignore[return-value]


class TopItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    visual_asset: str | None = Field(default=None)
    secondary_text: str | None = Field(default=None)
    metric: TopMetric | None = Field(default=None)
    comment: tuple[str, ...] = Field(default_factory=tuple)
    specs: tuple[TopSpecRow, ...] = Field(default_factory=tuple)

    @field_validator("visual_asset")
    @classmethod
    def _visual_relative(cls, v: str | None) -> str | None:
        return _validate_relative_path(v, "visual_asset")

    @field_validator("secondary_text")
    @classmethod
    def _secondary_strip(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = str(v).strip()
        return v if v else None

    @field_validator("comment", mode="before")
    @classmethod
    def _coerce_comment(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, (list, tuple)):
            return [str(x) for x in v]
        return [str(v)]

    @field_validator("specs", mode="before")
    @classmethod
    def _coerce_specs(cls, v: object) -> list[object]:
        if v is None:
            return []
        if not isinstance(v, (list, tuple)):
            raise ValueError("specs debe ser lista")
        out: list[object] = []
        for entry in v:
            if isinstance(entry, (list, tuple)) and len(entry) == 2:
                out.append({"label": str(entry[0]), "value": str(entry[1])})
            elif isinstance(entry, dict):
                out.append(entry)
            else:
                raise ValueError(f"spec inválido: {entry!r}")
        return out


class TopSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = Field(default=1, ge=1)
    title: tuple[str, ...]
    subtitle: str = Field(default="")
    audio: TopAudio = Field(default_factory=TopAudio)
    background_image_path: str | None = Field(default=None)
    final_hold_seconds: float = Field(default=5.0, ge=0)
    items: tuple[TopItem, ...]

    @field_validator("title", mode="before")
    @classmethod
    def _coerce_title(cls, v: object) -> list[str]:
        if isinstance(v, str):
            v = [v]
        if not isinstance(v, (list, tuple)) or not v:
            raise ValueError("title debe ser string o lista no vacía")
        out = [str(x).strip() for x in v if str(x).strip()]
        if not out:
            raise ValueError("title no puede estar vacío")
        return out

    @field_validator("background_image_path")
    @classmethod
    def _bg_relative(cls, v: str | None) -> str | None:
        return _validate_relative_path(v, "background_image_path")

    @field_validator("subtitle", mode="before")
    @classmethod
    def _coerce_subtitle(cls, v: object) -> str:
        return str(v) if v is not None else ""

    @field_validator("items")
    @classmethod
    def _validate_items(cls, v: tuple[TopItem, ...]) -> tuple[TopItem, ...]:
        if not v:
            raise ValueError("items no puede estar vacío")
        return v
