"""Casos de prueba de una historia y su revisión humana (RF-05 / CA-05).

Máquina de estados:
    pendiente --aprobar (solo si es válido)--> aprobado
    pendiente --descartar--------------------> descartado
    aprobado | descartado --volver a pendiente--> pendiente
La edición solo se permite en "pendiente" y siempre revalida el caso (RF-04).
"""

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.catalogo import Catalogo
from app.errors import ErrorNegocio, NoEncontrado
from app.models import CasoPrueba, HistoriaUsuario
from app.models.estados import EstadoCaso
from app.schemas.casos import CasoSalida
from app.services.validador import validar_gherkin

TITULO_MAX = 200
_LINEA_ESCENARIO = re.compile(r"^\s*(?:Escenario|Ejemplo)\s*:\s*(.+?)\s*$", re.MULTILINE)

# acción → (estados desde los que se permite, estado resultante)
TRANSICIONES: dict[str, tuple[frozenset[EstadoCaso], EstadoCaso]] = {
    "aprobar": (frozenset({EstadoCaso.PENDIENTE}), EstadoCaso.APROBADO),
    "descartar": (frozenset({EstadoCaso.PENDIENTE}), EstadoCaso.DESCARTADO),
    "pendiente": (
        frozenset({EstadoCaso.APROBADO, EstadoCaso.DESCARTADO}),
        EstadoCaso.PENDIENTE,
    ),
}
MENSAJES_TRANSICION = {
    "aprobar": "Solo se pueden aprobar casos pendientes: {codigo} está {estado}.",
    "descartar": "Solo se pueden descartar casos pendientes: {codigo} está {estado}.",
    "pendiente": "{codigo} ya está pendiente.",
}


def listar_casos(db: Session, historia_id: int) -> list[CasoSalida]:
    if db.get(HistoriaUsuario, historia_id) is None:
        raise NoEncontrado(f"La historia HU-{historia_id} no existe")
    casos = db.scalars(
        select(CasoPrueba).where(CasoPrueba.historia_id == historia_id).order_by(CasoPrueba.id)
    )
    return [CasoSalida.model_validate(caso) for caso in casos]


def cambiar_estado(db: Session, caso_id: int, accion: str) -> CasoSalida:
    caso = _obtener(db, caso_id)
    origenes, destino = TRANSICIONES[accion]
    if caso.estado not in origenes:
        mensaje = MENSAJES_TRANSICION[accion].format(codigo=caso.codigo, estado=caso.estado)
        raise ErrorNegocio(mensaje, status_code=409)
    if destino == EstadoCaso.APROBADO and not caso.valido:
        raise ErrorNegocio(
            f"Solo se aprueban casos válidos: corregí {caso.codigo} antes de aprobarlo.",
            status_code=409,
        )
    caso.estado = destino
    return _guardar(db, caso)


def editar_caso(db: Session, caso_id: int, gherkin: str, catalogo: Catalogo) -> CasoSalida:
    caso = _obtener(db, caso_id)
    if caso.estado != EstadoCaso.PENDIENTE:
        raise ErrorNegocio(
            f"Solo se pueden editar casos pendientes: volvé {caso.codigo} a pendiente "
            "para editarlo.",
            status_code=409,
        )
    texto = gherkin.strip() + "\n"
    errores = validar_gherkin(texto, catalogo)
    caso.gherkin = texto
    caso.valido = not errores
    caso.errores_validacion = errores or None
    # Si el escenario es válido, el título sale de su línea «Escenario:» (siempre coinciden).
    if not errores and (linea := _LINEA_ESCENARIO.search(texto)):
        caso.titulo = linea.group(1)[:TITULO_MAX]
    return _guardar(db, caso)


def _obtener(db: Session, caso_id: int) -> CasoPrueba:
    caso = db.get(CasoPrueba, caso_id)
    if caso is None:
        raise NoEncontrado(f"El caso CP-{caso_id} no existe")
    return caso


def _guardar(db: Session, caso: CasoPrueba) -> CasoSalida:
    # Explícito: onupdate no se dispara si los valores no cambiaron.
    caso.actualizado_en = func.now()
    caso.historia.actualizada_en = func.now()
    db.commit()
    db.refresh(caso)
    return CasoSalida.model_validate(caso)
