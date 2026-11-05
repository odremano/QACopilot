"""Catálogo de pasos del SUT (RF-02): carga y validación del YAML versionado.

Se carga una sola vez al iniciar el backend (lifespan). Si el archivo es inválido, el
arranque se aborta con el error registrado (CA-02).
"""

import re
from pathlib import Path
from typing import Annotated, Any, NamedTuple, Self

import yaml
from fastapi import Depends, Request
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    ValidationError,
    model_validator,
)

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


class Coincidencia(NamedTuple):
    paso: PasoCatalogo
    valor: str | None
    """Valor del parámetro "{texto}" tal como lo escribió el caso, o None si el paso no tiene."""


class Catalogo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sut: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    version: int = Field(ge=1)
    # Datos reales del SUT (usuarios, mensajes, productos) que el prompt le pasa al LLM para
    # que los valores de los pasos coincidan con la aplicación.
    contexto: str = ""
    pasos: list[PasoCatalogo] = Field(min_length=1)

    _expresiones: list[tuple[re.Pattern[str], PasoCatalogo]] = PrivateAttr(default_factory=list)

    def model_post_init(self, _contexto: Any) -> None:
        self._expresiones = [(_expresion(paso.patron), paso) for paso in self.pasos]

    def coincidir(self, texto: str) -> Coincidencia | None:
        """Paso del catálogo que coincide con el texto de un paso (sin la palabra clave).

        No distingue mayúsculas ni cantidad de espacios; el valor del parámetro se devuelve
        sin modificar. Lo usan el validador (RF-04) y el exportador (RF-06).
        """
        for expresion, paso in self._expresiones:
            if encontrado := expresion.fullmatch(texto.strip()):
                return Coincidencia(paso, encontrado.group(1) if encontrado.groups() else None)
        return None

    @model_validator(mode="after")
    def reglas_del_catalogo(self) -> Self:
        _sin_duplicados([p.id for p in self.pasos], "identificador duplicado")
        _sin_duplicados([p.patron.casefold() for p in self.pasos], "patrón duplicado")
        grupos = {p.grupo for p in self.pasos}
        faltantes = [g for g in GRUPOS_OBLIGATORIOS if g not in grupos]
        if faltantes:
            raise ValueError(f"faltan pasos de los grupos obligatorios: {', '.join(faltantes)}")
        return self


def _expresion(patron: str) -> re.Pattern[str]:
    """Regex del patrón: el parámetro acepta cualquier texto entre comillas (incluso vacío)."""
    partes = patron.split(f'"{PARAMETRO}"')
    return re.compile('"([^"]*)"'.join(_literal_flexible(p) for p in partes), re.IGNORECASE)


def _literal_flexible(texto: str) -> str:
    trozos = re.split(r"(\s+)", texto)
    return "".join(r"\s+" if t.isspace() else re.escape(t) for t in trozos if t)


def _sin_duplicados(valores: list[str], mensaje: str) -> None:
    vistos: set[str] = set()
    for valor in valores:
        if valor in vistos:
            raise ValueError(f"{mensaje}: '{valor}'")
        vistos.add(valor)


def describir_validacion(error: ValidationError) -> str:
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
        raise CatalogoInvalido(
            f"El catálogo {ruta} es inválido: {describir_validacion(exc)}"
        ) from exc


def get_catalogo(request: Request) -> Catalogo:
    return request.app.state.catalogo


CatalogoActual = Annotated[Catalogo, Depends(get_catalogo)]
