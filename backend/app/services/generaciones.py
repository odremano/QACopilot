"""Generación de casos con IA (RF-03), validación (RF-04), regeneración (RF-11) y límite diario
(RNF-08).

Cada intento fallido por formato se reintenta hasta 2 veces. Toda generación queda registrada,
salga bien o mal; si falla, la historia y sus casos anteriores no se tocan.
"""

import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.catalogo import Catalogo
from app.config import settings
from app.errors import ErrorNegocio, NoEncontrado
from app.models import CasoPrueba, Generacion, HistoriaUsuario
from app.models.estados import EstadoCaso, EstadoGeneracion, TipoCaso
from app.schemas.casos import GeneracionSalida
from app.services.llm import ErrorProveedor, ProveedorLLM
from app.services.prompt import VERSION_PROMPT, armar_mensajes
from app.services.validador import CasoValidado, RespuestaInvalida, validar_respuesta

logger = logging.getLogger(__name__)

MAX_INTENTOS = 3  # 1 intento + 2 reintentos (RF-04)
MIN_CASOS, MAX_CASOS = 3, 8
# Argentina no tiene horario de verano: el "día" del límite empieza a las 00:00 (UTC-3).
ZONA_LIMITE = timezone(timedelta(hours=-3))


def generar_casos(
    db: Session, historia_id: int, proveedor: ProveedorLLM, catalogo: Catalogo
) -> GeneracionSalida:
    historia = db.get(HistoriaUsuario, historia_id)
    if historia is None:
        raise NoEncontrado(f"La historia HU-{historia_id} no existe")
    _verificar_limite_diario(db)

    mensajes = armar_mensajes(historia, catalogo)
    intentos: list[dict] = []
    casos: list[CasoValidado] | None = None
    error: str | None = None
    inicio = time.monotonic()
    for numero in range(1, MAX_INTENTOS + 1):
        try:
            contenido = proveedor.completar(mensajes, historia)
        except ErrorProveedor as exc:
            intentos.append({"contenido": None, "error": exc.mensaje})
            error = exc.mensaje
            break
        try:
            casos = validar_respuesta(contenido, catalogo)
            _verificar_reglas(casos)
        except RespuestaInvalida as exc:
            intentos.append({"contenido": contenido, "error": exc.mensaje, "detalle": exc.detalle})
            logger.info("Intento %d de generación para HU-%d: %s", numero, historia_id, exc)
            casos = None
            error = f"{exc.mensaje} Se intentó {MAX_INTENTOS} veces."
            continue
        intentos.append({"contenido": contenido, "error": None})
        error = None
        break
    duracion_ms = round((time.monotonic() - inicio) * 1000)

    generacion = Generacion(
        historia_id=historia_id,
        proveedor=proveedor.nombre,
        modelo=proveedor.modelo,
        version_prompt=VERSION_PROMPT,
        estado=EstadoGeneracion.OK if casos is not None else EstadoGeneracion.ERROR,
        duracion_ms=duracion_ms,
        respuesta_cruda={"intentos": intentos},
        mensaje_error=error,
    )
    db.add(generacion)
    if casos is None:
        db.commit()
        logger.warning("Falló la generación para HU-%d: %s", historia_id, error)
        raise ErrorNegocio(error or "No se pudieron generar casos.", status_code=502)

    # RF-11: los pendientes anteriores se reemplazan; aprobados y descartados se conservan.
    db.execute(
        delete(CasoPrueba).where(
            CasoPrueba.historia_id == historia_id,
            CasoPrueba.estado == EstadoCaso.PENDIENTE,
        )
    )
    nuevos = [
        CasoPrueba(
            historia_id=historia_id,
            generacion=generacion,
            titulo=caso.titulo,
            tipo=caso.tipo,
            gherkin=caso.gherkin,
            estado=EstadoCaso.PENDIENTE,
            valido=caso.valido,
            errores_validacion=caso.errores or None,
        )
        for caso in casos
    ]
    db.add_all(nuevos)
    historia.actualizada_en = func.now()
    db.commit()
    db.refresh(generacion)
    return GeneracionSalida.model_validate(generacion)


def _verificar_reglas(casos: list[CasoValidado]) -> None:
    """Reglas de RF-03 sobre la generación completa; si no se cumplen, se reintenta."""
    if not MIN_CASOS <= len(casos) <= MAX_CASOS:
        raise RespuestaInvalida(
            f"El modelo propuso {len(casos)} casos y deben ser entre {MIN_CASOS} y {MAX_CASOS}."
        )
    tipos = {caso.tipo for caso in casos}
    if not {TipoCaso.POSITIVO, TipoCaso.NEGATIVO} <= tipos:
        raise RespuestaInvalida("El modelo no propuso al menos un caso positivo y uno negativo.")


def _verificar_limite_diario(db: Session) -> None:
    limite = settings.daily_generation_limit
    if limite <= 0:
        return
    hoy = datetime.now(ZONA_LIMITE).replace(hour=0, minute=0, second=0, microsecond=0)
    realizadas = db.scalar(
        select(func.count()).select_from(Generacion).where(Generacion.creada_en >= hoy)
    )
    if realizadas >= limite:
        raise ErrorNegocio(
            f"Se alcanzó el límite diario de {limite} generaciones. Probá de nuevo mañana.",
            status_code=429,
        )
