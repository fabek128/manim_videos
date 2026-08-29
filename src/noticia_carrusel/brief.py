"""Esquema validable del brief de investigación.

Un brief documenta lo que se investigó sobre un tema antes de redactar
cualquier caption: qué está confirmado, qué no, qué se contradice entre
fuentes y por qué importa. Ver `docs/agent-mode.md` §3 y §6.
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field, model_validator

EstadoBrief = Literal["confirmado", "rumor", "en_curso", "desmentido"]
TipoFuente = Literal["primaria", "secundaria"]


class Fuente(BaseModel):
    url: str
    medio: str
    fecha: dt.date
    tipo: TipoFuente


class Brief(BaseModel):
    tema: str
    estado: EstadoBrief
    hechos: list[str] = Field(default_factory=list)
    fuentes: list[Fuente] = Field(default_factory=list)
    sin_confirmar: list[str] = Field(default_factory=list)
    contradicciones: list[str] = Field(default_factory=list)
    porque_importa: str = ""

    @model_validator(mode="after")
    def _validar_confirmacion(self) -> "Brief":
        if self.estado == "confirmado":
            primarias = [f for f in self.fuentes if f.tipo == "primaria"]
            if len(primarias) < 2:
                raise ValueError(
                    "estado='confirmado' requiere al menos 2 fuentes primarias; "
                    f"tiene {len(primarias)}"
                )
        if self.estado != "desmentido" and not self.hechos:
            raise ValueError("El brief necesita al menos un hecho en 'hechos'")
        return self
