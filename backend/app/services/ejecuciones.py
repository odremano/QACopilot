"""Ejecución de los casos aprobados contra el SUT y registro de resultados (RF-07, RF-08).

Al iniciar, la ejecución queda «en curso» y la API responde enseguida; Playwright corre en
segundo plano con su propia sesión de base. Una sola ejecución a la vez: lo garantiza un
índice único parcial (ux_ejecucion_una_en_curso), así que ni dos pedidos simultáneos pueden
saltear la regla. Lo que se ejecuta es el mismo .spec.ts que se descarga (RF-06).
"""

import logging
from pathlib import Path

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload, sessionmaker

from app.catalogo import Catalogo
from app.config import settings
from app.errors import ErrorNegocio, NoEncontrado
from app.models import Ejecucion, ResultadoCaso
from app.models.estados import EstadoEjecucion, EstadoResultado
from app.services import exportador
from app.services.reporte_playwright import (
    ResultadoTest,
    errores_globales,
    leer_reporte,
    limpiar,
)
from app.services.runner import Runner, SalidaRunner, TiempoAgotado

logger = logging.getLogger(__name__)

INDICE_EN_CURSO = "ux_ejecucion_una_en_curso"
REINICIO = "El backend se reinició mientras la ejecución estaba en curso."
NO_EJECUTADO = "No se ejecutó: el test no aparece en el reporte de Playwright."


def directorio_evidencias() -> Path:
    return Path(settings.evidencias_dir)


def carpeta_ejecucion(ejecucion_id: int) -> Path:
    return directorio_evidencias() / "ejecuciones" / str(ejecucion_id)


def iniciar_ejecucion(
    db: Session, historia_id: int, catalogo: Catalogo
) -> tuple[Ejecucion, exportador.ArchivoSpec]:
    archivo = exportador.exportar_historia(db, historia_id, catalogo)
    _rechazar_si_hay_otra_en_curso(db)
    ejecucion = Ejecucion(
        historia_id=historia_id, estado=EstadoEjecucion.EN_CURSO, total=len(archivo.casos)
    )
    db.add(ejecucion)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if INDICE_EN_CURSO in str(exc.orig):
            _rechazar_si_hay_otra_en_curso(db)
        raise
    db.refresh(ejecucion)
    return ejecucion, archivo


def correr_ejecucion(
    ejecucion_id: int,
    archivo: exportador.ArchivoSpec,
    sesiones: sessionmaker[Session],
    runner: Runner,
) -> None:
    """Tarea en segundo plano: corre Playwright y guarda los resultados. Nunca queda colgada."""
    casos = [caso.id for caso in archivo.casos]
    try:
        salida = runner.ejecutar(archivo.nombre, archivo.contenido, carpeta_ejecucion(ejecucion_id))
    except TiempoAgotado as exc:
        _terminar_con_error(sesiones, ejecucion_id, str(exc))
        return
    except Exception as exc:
        logger.exception("No se pudo correr Playwright para la ejecución %d", ejecucion_id)
        _terminar_con_error(sesiones, ejecucion_id, f"No se pudo correr Playwright: {exc}")
        return
    try:
        _registrar_resultados(sesiones, ejecucion_id, casos, salida)
    except Exception as exc:
        logger.exception("No se pudieron guardar los resultados de la ejecución %d", ejecucion_id)
        _terminar_con_error(sesiones, ejecucion_id, f"No se pudo leer el reporte: {exc}")


def listar_ejecuciones(db: Session, historia_id: int | None = None) -> list[Ejecucion]:
    consulta = (
        select(Ejecucion).options(joinedload(Ejecucion.historia)).order_by(Ejecucion.id.desc())
    )
    if historia_id is not None:
        consulta = consulta.where(Ejecucion.historia_id == historia_id)
    return list(db.scalars(consulta))


def obtener_ejecucion(db: Session, ejecucion_id: int) -> Ejecucion:
    ejecucion = db.scalar(
        select(Ejecucion)
        .where(Ejecucion.id == ejecucion_id)
        .options(
            joinedload(Ejecucion.historia),
            selectinload(Ejecucion.resultados).joinedload(ResultadoCaso.caso),
        )
    )
    if ejecucion is None:
        raise NoEncontrado(f"La ejecución {ejecucion_id} no existe")
    return ejecucion


def ruta_captura(db: Session, resultado_id: int) -> Path:
    resultado = db.get(ResultadoCaso, resultado_id)
    if resultado is None or not resultado.ruta_captura:
        raise NoEncontrado(f"No hay captura para el resultado {resultado_id}")
    base = directorio_evidencias().resolve()
    ruta = (base / resultado.ruta_captura).resolve()
    # La ruta sale de la base, pero igual se verifica que no escape de las evidencias.
    if not ruta.is_relative_to(base) or not ruta.is_file():
        raise NoEncontrado(f"No hay captura para el resultado {resultado_id}")
    return ruta


def marcar_interrumpidas(db: Session) -> int:
    """Al arrancar el backend: las ejecuciones que quedaron «en curso» se cortaron."""
    marcadas = db.execute(
        update(Ejecucion)
        .where(Ejecucion.estado == EstadoEjecucion.EN_CURSO)
        .values(estado=EstadoEjecucion.ERROR, finalizada_en=func.now(), log=REINICIO)
    ).rowcount
    db.commit()
    return marcadas


def _rechazar_si_hay_otra_en_curso(db: Session) -> None:
    en_curso = db.scalar(
        select(Ejecucion)
        .where(Ejecucion.estado == EstadoEjecucion.EN_CURSO)
        .options(joinedload(Ejecucion.historia))
    )
    if en_curso is not None:
        raise ErrorNegocio(
            f"Ya hay una ejecución en curso (ejecución {en_curso.id} de "
            f"{en_curso.historia.codigo}). Esperá a que termine para iniciar otra.",
            status_code=409,
        )


def _registrar_resultados(
    sesiones: sessionmaker[Session], ejecucion_id: int, casos: list[int], salida: SalidaRunner
) -> None:
    if salida.reporte is None:
        _terminar_con_error(
            sesiones,
            ejecucion_id,
            "Playwright no generó el reporte.\n\n" + limpiar(salida.log),
        )
        return
    errores = errores_globales(salida.reporte)
    por_caso = {r.caso_id: r for r in leer_reporte(salida.reporte) if r.caso_id in casos}
    if errores and not por_caso:
        _terminar_con_error(sesiones, ejecucion_id, "\n\n".join([*errores, limpiar(salida.log)]))
        return

    resultados = [
        _resultado_caso(ejecucion_id, caso_id, por_caso.get(caso_id)) for caso_id in casos
    ]
    estados = [resultado.estado for resultado in resultados]
    with sesiones() as db:
        db.add_all(resultados)
        ejecucion = db.get(Ejecucion, ejecucion_id)
        ejecucion.total = len(resultados)
        ejecucion.aprobados = estados.count(EstadoResultado.APROBADO)
        ejecucion.fallidos = estados.count(EstadoResultado.FALLIDO)
        ejecucion.omitidos = estados.count(EstadoResultado.OMITIDO)
        ejecucion.estado = EstadoEjecucion.FINALIZADA
        ejecucion.finalizada_en = func.now()
        ejecucion.log = limpiar(salida.log)
        db.commit()


def _resultado_caso(ejecucion_id: int, caso_id: int, test: ResultadoTest | None) -> ResultadoCaso:
    if test is None:
        return ResultadoCaso(
            ejecucion_id=ejecucion_id,
            caso_id=caso_id,
            estado=EstadoResultado.OMITIDO,
            mensaje_error=NO_EJECUTADO,
        )
    return ResultadoCaso(
        ejecucion_id=ejecucion_id,
        caso_id=caso_id,
        estado=test.estado,
        duracion_ms=test.duracion_ms,
        mensaje_error=test.mensaje_error,
        ruta_captura=_relativa(test.captura),
    )


def _terminar_con_error(sesiones: sessionmaker[Session], ejecucion_id: int, log: str) -> None:
    with sesiones() as db:
        ejecucion = db.get(Ejecucion, ejecucion_id)
        ejecucion.estado = EstadoEjecucion.ERROR
        ejecucion.finalizada_en = func.now()
        ejecucion.log = log
        db.commit()


def _relativa(captura: Path | None) -> str | None:
    """Ruta de la captura relativa a la carpeta de evidencias (así se guarda en la base)."""
    if captura is None:
        return None
    try:
        return captura.resolve().relative_to(directorio_evidencias().resolve()).as_posix()
    except ValueError:
        logger.warning("La captura %s está fuera de la carpeta de evidencias", captura)
        return None
