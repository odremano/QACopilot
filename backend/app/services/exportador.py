"""Exportación de los casos aprobados a un .spec.ts de Playwright (RF-06 / CA-06).

El TypeScript sale solo de las plantillas del catálogo (DEC-04, RNF-05). Del caso se toman
el título, el texto de cada paso y los valores de sus parámetros, y todos entran al archivo
como literales de cadena escapados con json.dumps: un literal JSON es un literal de cadena
válido en TypeScript, así que ningún texto del caso puede cerrar la cadena ni inyectar código.
El mismo archivo es el que se descarga y el que ejecuta el runner (RF-07).
"""

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalogo import PARAMETRO, Catalogo
from app.errors import ErrorNegocio, NoEncontrado
from app.models import CasoPrueba, HistoriaUsuario
from app.models.estados import EstadoCaso
from app.services.validador import pasos_del_escenario, validar_gherkin

SANGRIA_PASO = " " * 6


@dataclass(frozen=True)
class ArchivoSpec:
    nombre: str
    contenido: str
    casos: list[CasoPrueba]


def exportar_historia(db: Session, historia_id: int, catalogo: Catalogo) -> ArchivoSpec:
    historia = db.get(HistoriaUsuario, historia_id)
    if historia is None:
        raise NoEncontrado(f"La historia HU-{historia_id} no existe")
    casos = list(
        db.scalars(
            select(CasoPrueba)
            .where(
                CasoPrueba.historia_id == historia_id,
                CasoPrueba.estado == EstadoCaso.APROBADO,
            )
            .order_by(CasoPrueba.id)
        )
    )
    if not casos:
        raise ErrorNegocio(
            f"{historia.codigo} no tiene casos aprobados: aprobá al menos uno para exportar.",
            status_code=409,
        )
    return ArchivoSpec(
        nombre=f"{historia.codigo}.spec.ts",
        contenido=generar_spec(historia, casos, catalogo),
        casos=casos,
    )


def generar_spec(historia: HistoriaUsuario, casos: list[CasoPrueba], catalogo: Catalogo) -> str:
    # Los comentarios solo llevan códigos y la versión del catálogo, nunca texto del usuario.
    lineas = [
        f"// Generado por QA Copilot para {historia.codigo} "
        f"(catálogo {catalogo.sut} v{catalogo.version}).",
        "// Cada paso Gherkin se traduce con la plantilla del catálogo; no editar a mano.",
        "import { test, expect } from '@playwright/test';",
        "",
        f"test.describe({_literal(f'[{historia.codigo}] {historia.titulo}')}, () => {{",
    ]
    for indice, caso in enumerate(casos):
        if indice:
            lineas.append("")
        lineas += _test(caso, catalogo)
    lineas += ["});", ""]
    return "\n".join(lineas)


def _test(caso: CasoPrueba, catalogo: Catalogo) -> list[str]:
    # Un caso aprobado era válido al aprobarse, pero el catálogo pudo cambiar después.
    if errores := validar_gherkin(caso.gherkin, catalogo):
        raise ErrorNegocio(
            f"{caso.codigo} está aprobado pero ya no es válido con el catálogo actual: "
            f"{errores[0]} Volvelo a pendiente y corregilo para poder exportar.",
            status_code=409,
        )
    lineas = [f"  test({_literal(f'[{caso.codigo}] {caso.titulo}')}, async ({{ page }}) => {{"]
    for palabra_clave, texto in pasos_del_escenario(caso.gherkin):
        coincidencia = catalogo.coincidir(texto)
        assert coincidencia is not None  # validar_gherkin ya lo garantizó
        valor = coincidencia.valor
        lineas.append(f"    await test.step({_literal(f'{palabra_clave} {texto}')}, async () => {{")
        for linea in coincidencia.paso.plantilla.split("\n"):
            # str.replace y no str.format: las plantillas tienen llaves de JavaScript.
            if valor is not None:
                linea = linea.replace(PARAMETRO, _literal(valor))
            lineas.append(f"{SANGRIA_PASO}{linea}")
        lineas.append("    });")
    lineas.append("  });")
    return lineas


def _literal(texto: str) -> str:
    """Literal de cadena de TypeScript con el texto escapado.

    Los separadores U+2028 y U+2029 se escapan también: son válidos dentro de una cadena,
    pero los editores y varias herramientas los toman como saltos de línea.
    """
    literal = json.dumps(texto, ensure_ascii=False)
    return literal.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
