from typing import Literal

from pydantic import BaseModel


class EstadoLlm(BaseModel):
    proveedor: str
    modelo: str
    configurado: bool


class Salud(BaseModel):
    estado: Literal["ok", "degradado"]
    base_de_datos: Literal["ok", "error"]
    llm: EstadoLlm
    version: str
