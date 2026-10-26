from fastapi import APIRouter, status

from app.db import DbSession
from app.schemas.errores import ErrorDetalle
from app.schemas.historias import HistoriaDetalle, HistoriaEntrada, HistoriaResumen
from app.services import historias as servicio

router = APIRouter(prefix="/historias", tags=["Historias"])

NO_ENCONTRADA = {404: {"model": ErrorDetalle, "description": "La historia no existe"}}


@router.get(
    "",
    response_model=list[HistoriaResumen],
    summary="Listar historias",
    description=(
        "Devuelve las historias ordenadas por fecha de actualización (más recientes primero), "
        "cada una con la cantidad de casos por estado y de casos inválidos."
    ),
)
def listar(db: DbSession) -> list[HistoriaResumen]:
    return servicio.listar_historias(db)


@router.post(
    "",
    response_model=HistoriaDetalle,
    status_code=status.HTTP_201_CREATED,
    summary="Crear historia",
    description=(
        "Crea una historia de usuario. El título (hasta 120 caracteres) y la descripción son "
        "obligatorios; los criterios de aceptación son opcionales."
    ),
)
def crear(datos: HistoriaEntrada, db: DbSession) -> HistoriaDetalle:
    return servicio.crear_historia(db, datos)


@router.get(
    "/{historia_id}",
    response_model=HistoriaDetalle,
    summary="Ver historia",
    description="Devuelve el detalle de una historia con el resumen de sus casos.",
    responses=NO_ENCONTRADA,
)
def obtener(historia_id: int, db: DbSession) -> HistoriaDetalle:
    return servicio.obtener_historia(db, historia_id)


@router.put(
    "/{historia_id}",
    response_model=HistoriaDetalle,
    summary="Editar historia",
    description=(
        "Reemplaza título, descripción y criterios de aceptación. Aplica las mismas "
        "validaciones que el alta y actualiza la fecha de actualización."
    ),
    responses=NO_ENCONTRADA,
)
def editar(historia_id: int, datos: HistoriaEntrada, db: DbSession) -> HistoriaDetalle:
    return servicio.editar_historia(db, historia_id, datos)
