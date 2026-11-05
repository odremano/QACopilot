"""Validación de los casos de prueba (RF-04 / CA-04).

Tres niveles: el esquema JSON de la respuesta del LLM (Pydantic), la sintaxis Gherkin
(parser oficial) y la pertenencia de cada paso al catálogo. El LLM devuelve título, tipo y
lista de pasos (Anexo B); el sistema arma el «Escenario:» y lo valida. Una respuesta que no
cumple el esquema es un error de la generación (se reintenta); un caso con Gherkin o pasos
inválidos se guarda igual, marcado como inválido y con el detalle de sus errores.
"""

import re
from dataclasses import dataclass
from typing import Any

from gherkin.errors import CompositeParserException, ParserError, UnexpectedEOFException
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.catalogo import Catalogo, describir_validacion
from app.models.estados import TipoCaso

# El caso guarda solo el escenario; la cabecera se agrega para parsearlo en español.
CABECERA = "# language: es\nCaracterística: caso\n"
LINEAS_CABECERA = CABECERA.count("\n")

_CARACTERISTICA = re.compile(r"^\s*Característica\s*:", re.IGNORECASE | re.MULTILINE)


class RespuestaInvalida(Exception):
    """La respuesta del LLM está vacía, no es JSON o no respeta el esquema (se reintenta)."""

    def __init__(self, mensaje: str, detalle: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalle = detalle


class CasoPropuesto(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=1, max_length=200)
    tipo: TipoCaso
    pasos: list[str] = Field(min_length=1)

    @field_validator("tipo", mode="before")
    @classmethod
    def normalizar_tipo(cls, valor: Any) -> Any:
        # Tolera "Positivo" o "límite": el valor guardado siempre es el del StrEnum.
        if isinstance(valor, str):
            return valor.strip().casefold().replace("í", "i")
        return valor

    @property
    def gherkin(self) -> str:
        return armar_gherkin(self.titulo, self.pasos)


class RespuestaModelo(BaseModel):
    casos: list[CasoPropuesto] = Field(min_length=1)


@dataclass
class CasoValidado:
    titulo: str
    tipo: TipoCaso
    gherkin: str
    errores: list[str]

    @property
    def valido(self) -> bool:
        return not self.errores


def validar_respuesta(contenido: str, catalogo: Catalogo) -> list[CasoValidado]:
    """Valida la respuesta cruda del LLM. Lanza RespuestaInvalida si no se puede usar."""
    if not contenido or not contenido.strip():
        raise RespuestaInvalida("El modelo devolvió una respuesta vacía.")
    try:
        respuesta = RespuestaModelo.model_validate_json(contenido)
    except ValidationError as exc:
        tipos = {error["type"] for error in exc.errors()}
        if "json_invalid" in tipos:
            mensaje = "La respuesta del modelo no es JSON válido."
        elif exc.errors()[0]["loc"] == ("casos",) and "too_short" in tipos:
            mensaje = "El modelo no propuso ningún caso."
        else:
            mensaje = "La respuesta del modelo no respeta el formato esperado."
        raise RespuestaInvalida(mensaje, detalle=describir_validacion(exc)) from exc
    return [
        CasoValidado(
            titulo=caso.titulo,
            tipo=caso.tipo,
            gherkin=caso.gherkin,
            errores=validar_gherkin(caso.gherkin, catalogo),
        )
        for caso in respuesta.casos
    ]


def armar_gherkin(titulo: str, pasos: list[str]) -> str:
    """Texto que se guarda en caso_prueba.gherkin: un escenario con un paso por línea."""
    titulo = " ".join(titulo.split())
    return f"Escenario: {titulo}\n" + "".join(f"  {paso.strip()}\n" for paso in pasos)


def validar_gherkin(texto: str, catalogo: Catalogo) -> list[str]:
    """Errores de un caso (lista vacía si es válido). También se usa al editar (RF-05)."""
    if not texto.strip():
        return ["El caso no tiene contenido Gherkin."]
    if _CARACTERISTICA.search(texto):
        return ["El caso debe contener solo el escenario, sin la línea «Característica:»."]
    try:
        documento = Parser().parse(TokenScanner(CABECERA + texto))
    except CompositeParserException as exc:
        return [_error_de_sintaxis(error, texto) for error in exc.errors]
    except ParserError as exc:
        return [_error_de_sintaxis(exc, texto)]

    hijos = documento["feature"]["children"]
    escenarios = [hijo["scenario"] for hijo in hijos if "scenario" in hijo]
    # El parser toma las líneas sueltas como descripción libre: acá se rechazan.
    errores = _texto_libre(documento["feature"]["description"], "antes del escenario")
    if len(escenarios) != len(hijos):
        errores.append("El caso no admite «Antecedentes» ni «Regla»: solo un escenario.")
    if not escenarios:
        return [*errores, "El caso no tiene un «Escenario:»."]
    if len(escenarios) > 1:
        return [*errores, f"El caso tiene {len(escenarios)} escenarios y debe tener uno solo."]

    escenario = escenarios[0]
    errores += _texto_libre(escenario["description"], "que no es un paso")
    if escenario["examples"] or escenario["keyword"].casefold().startswith("esquema"):
        errores.append(
            "No se admiten «Esquema del escenario» ni «Ejemplos»: usá valores concretos."
        )
    if not escenario["steps"]:
        errores.append("El escenario no tiene pasos.")
    for numero, paso in enumerate(escenario["steps"], start=1):
        linea = f"{paso['keyword']}{paso['text']}"
        if "dataTable" in paso or "docString" in paso:
            errores.append(f"Paso {numero} («{linea}»): no se admiten tablas ni bloques de texto.")
        elif catalogo.coincidir(paso["text"]) is None:
            errores.append(f"Paso {numero}: «{linea}» no coincide con ningún paso del catálogo.")
    return errores


def _texto_libre(descripcion: str, donde: str) -> list[str]:
    lineas = [linea.strip() for linea in descripcion.splitlines() if linea.strip()]
    if not lineas:
        return []
    return [
        f"Hay texto {donde}: «{lineas[0]}». "
        "Los pasos empiezan con Dado, Cuando, Entonces, Y o Pero."
    ]


def _error_de_sintaxis(error: Exception, texto: str) -> str:
    if isinstance(error, UnexpectedEOFException):
        return "El Gherkin termina de forma incompleta (¿un bloque de texto sin cerrar?)."
    ubicacion = getattr(error, "location", None) or {}
    numero = (ubicacion.get("line") or 0) - LINEAS_CABECERA
    lineas = texto.splitlines()
    if 1 <= numero <= len(lineas):
        return f"Línea {numero}: «{lineas[numero - 1].strip()}» no es una línea Gherkin válida."
    return f"Sintaxis Gherkin inválida: {error}"
