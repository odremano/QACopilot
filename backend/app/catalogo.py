"""Catálogo de pasos del SUT (RF-02): carga y validación del YAML versionado.

Se carga una sola vez al iniciar el backend (lifespan). Si el archivo es inválido, el
arranque se aborta con el error registrado (CA-02).
"""

import re
from pathlib import Path
from typing import Annotated, Self

import yaml
from fastapi import Depends, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

PARAMETRO = "{texto}"
GRUPOS_OBLIGATORIOS = ("inicio de sesión", "inventario", "carrito", "checkout")
RAIZ_BACKEND = Path(__file__).resolve().parent.parent

_LLAVES = re.compile(r"\{[^}]*\}")


class CatalogoInvalido(Exception):
    """El archivo del catálogo no existe, no es YAML válido o no cumple las reglas."""


class PasoCatalogo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    grupo: str = Field(min_length=1)
    patron: str = Field(min_length=1)
    plantilla: str = Field(min_length=1)

    @model_validator(mode="after")
    def parametro_consistente(self) -> Self:
        llaves = _LLAVES.findall(self.patron)
        if any(llave != PARAMETRO for llave in llaves):
            raise ValueError(f"el patrón solo admite el parámetro {PARAMETRO}")
        if len(llaves) > 1:
            raise ValueError("el patrón admite como máximo un parámetro")
        if llaves and f'"{PARAMETRO}"' not in self.patron:
            raise ValueError(f'el parámetro debe ir entre comillas: "{PARAMETRO}"')
        en_plantilla = PARAMETRO in self.plantilla
        if llaves and not en_plantilla:
            raise ValueError(f"el patrón tiene {PARAMETRO} pero la plantilla no lo usa")
        if not llaves and en_plantilla:
            raise ValueError(f"la plantilla usa {PARAMETRO} pero el patrón no lo tiene")
        return self


class Catalogo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sut: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    version: int = Field(ge=1)
    pasos: list[PasoCatalogo] = Field(min_length=1)

    @model_validator(mode="after")
    def reglas_del_catalogo(self) -> Self:
        _sin_duplicados([p.id for p in self.pasos], "identificador duplicado")
        _sin_duplicados([p.patron.casefold() for p in self.pasos], "patrón duplicado")
        grupos = {p.grupo for p in self.pasos}
        faltantes = [g for g in GRUPOS_OBLIGATORIOS if g not in grupos]
        if faltantes:
            raise ValueError(f"faltan pasos de los grupos obligatorios: {', '.join(faltantes)}")
        return self


def _sin_duplicados(valores: list[str], mensaje: str) -> None:
    vistos: set[str] = set()
    for valor in valores:
        if valor in vistos:
            raise ValueError(f"{mensaje}: '{valor}'")
        vistos.add(valor)


def _describir(error: ValidationError) -> str:
    lineas = []
    for detalle in error.errors():
        ubicacion = "".join(
            f"[{parte}]" if isinstance(parte, int) else f".{parte}" for parte in detalle["loc"]
        ).lstrip(".")
        mensaje = detalle["msg"].removeprefix("Value error, ")
        lineas.append(f"{ubicacion}: {mensaje}" if ubicacion else mensaje)
    return "; ".join(lineas)


def cargar_catalogo(ruta: str | Path) -> Catalogo:
    ruta = Path(ruta)
    if not ruta.is_absolute():
        ruta = RAIZ_BACKEND / ruta
    try:
        datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogoInvalido(f"No existe el archivo del catálogo: {ruta}") from exc
    except yaml.YAMLError as exc:
        raise CatalogoInvalido(f"El catálogo {ruta} no es YAML válido: {exc}") from exc
    if not isinstance(datos, dict):
        raise CatalogoInvalido(f"El catálogo {ruta} debe ser un objeto con sut, version y pasos")
    try:
        return Catalogo.model_validate(datos)
    except ValidationError as exc:
        raise CatalogoInvalido(f"El catálogo {ruta} es inválido: {_describir(exc)}") from exc


def get_catalogo(request: Request) -> Catalogo:
    return request.app.state.catalogo


CatalogoActual = Annotated[Catalogo, Depends(get_catalogo)]
