"""Lógica de negocio de las historias de usuario (RF-01) y su resumen para el panel (RF-09)."""

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session

from app.errors import NoEncontrado
from app.models import CasoPrueba, Ejecucion, HistoriaUsuario
from app.models.estados import EstadoCaso
from app.schemas.ejecuciones import EjecucionResumen
from app.schemas.historias import HistoriaDetalle, HistoriaEntrada, HistoriaResumen, ResumenCasos

COLUMNAS_EJECUCION = (
    "id",
    "estado",
    "iniciada_en",
    "finalizada_en",
    "total",
    "aprobados",
    "fallidos",
    "omitidos",
)


def _consulta_con_resumen() -> Select:
    """Historias con sus casos contados por estado y su última ejecución, en una sola consulta.

    La última ejecución sale de un DISTINCT ON (PostgreSQL): una fila por historia, la de
    mayor id. Solo se traen los totales, no el log.
    """

    def contar(condicion):
        return func.count().filter(condicion)

    resumen = (
        select(
            CasoPrueba.historia_id,
            contar(CasoPrueba.estado == EstadoCaso.PENDIENTE).label("pendiente"),
            contar(CasoPrueba.estado == EstadoCaso.APROBADO).label("aprobado"),
            contar(CasoPrueba.estado == EstadoCaso.DESCARTADO).label("descartado"),
            contar(CasoPrueba.valido.is_(False)).label("invalidos"),
        )
        .group_by(CasoPrueba.historia_id)
        .subquery()
    )
    ultima = (
        select(
            Ejecucion.historia_id,
            *(getattr(Ejecucion, columna).label(f"ej_{columna}") for columna in COLUMNAS_EJECUCION),
        )
        .ext(distinct_on(Ejecucion.historia_id))
        .order_by(Ejecucion.historia_id, Ejecucion.id.desc())
        .subquery()
    )
    consulta = select(
        HistoriaUsuario,
        func.coalesce(resumen.c.pendiente, 0).label("pendiente"),
        func.coalesce(resumen.c.aprobado, 0).label("aprobado"),
        func.coalesce(resumen.c.descartado, 0).label("descartado"),
        func.coalesce(resumen.c.invalidos, 0).label("invalidos"),
        *(ultima.c[f"ej_{columna}"] for columna in COLUMNAS_EJECUCION),
    )
    return consulta.outerjoin(resumen, resumen.c.historia_id == HistoriaUsuario.id).outerjoin(
        ultima, ultima.c.historia_id == HistoriaUsuario.id
    )


def _resumen(fila) -> ResumenCasos:
    return ResumenCasos(
        pendiente=fila.pendiente,
        aprobado=fila.aprobado,
        descartado=fila.descartado,
        invalidos=fila.invalidos,
    )


def _ultima_ejecucion(fila) -> EjecucionResumen | None:
    if fila.ej_id is None:
        return None
    return EjecucionResumen(
        **{columna: getattr(fila, f"ej_{columna}") for columna in COLUMNAS_EJECUCION}
    )


def _con_resumen(esquema, fila):
    return esquema.model_validate(fila.HistoriaUsuario).model_copy(
        update={"resumen_casos": _resumen(fila), "ultima_ejecucion": _ultima_ejecucion(fila)}
    )


def listar_historias(db: Session) -> list[HistoriaResumen]:
    filas = db.execute(
        _consulta_con_resumen().order_by(
            HistoriaUsuario.actualizada_en.desc(), HistoriaUsuario.id.desc()
        )
    ).all()
    return [_con_resumen(HistoriaResumen, fila) for fila in filas]


def obtener_historia(db: Session, historia_id: int) -> HistoriaDetalle:
    fila = db.execute(
        _consulta_con_resumen().where(HistoriaUsuario.id == historia_id)
    ).one_or_none()
    if fila is None:
        raise NoEncontrado(f"La historia HU-{historia_id} no existe")
    return _con_resumen(HistoriaDetalle, fila)


def crear_historia(db: Session, datos: HistoriaEntrada) -> HistoriaDetalle:
    historia = HistoriaUsuario(**datos.model_dump())
    db.add(historia)
    db.commit()
    db.refresh(historia)
    return HistoriaDetalle.model_validate(historia)


def editar_historia(db: Session, historia_id: int, datos: HistoriaEntrada) -> HistoriaDetalle:
    historia = db.get(HistoriaUsuario, historia_id)
    if historia is None:
        raise NoEncontrado(f"La historia HU-{historia_id} no existe")
    for campo, valor in datos.model_dump().items():
        setattr(historia, campo, valor)
    # Explícito: onupdate no se dispara si los valores no cambiaron.
    historia.actualizada_en = func.now()
    db.commit()
    return obtener_historia(db, historia_id)
