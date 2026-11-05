from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, status
from fastapi.responses import FileResponse

from app.catalogo import CatalogoActual
from app.db import DbSession, FabricaSesiones
from app.schemas.ejecuciones import EjecucionDetalle, EjecucionSalida
from app.schemas.errores import ErrorDetalle
from app.services import ejecuciones as servicio
from app.services.runner import RunnerActual

router = APIRouter(tags=["Ejecuciones"])


@router.post(
    "/historias/{historia_id}/ejecuciones",
    response_model=EjecucionSalida,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar los casos aprobados",
    description=(
        "Inicia la ejecución de los casos aprobados de la historia contra el SUT con "
        "Playwright (RF-07). Responde enseguida con la ejecución «en curso»; Playwright corre "
        "en segundo plano y al terminar la ejecución queda «finalizada» (o «error») con el "
        "resultado de cada caso (RF-08). Solo puede haber una ejecución en curso a la vez."
    ),
    responses={
        404: {"model": ErrorDetalle, "description": "La historia no existe"},
        409: {
            "model": ErrorDetalle,
            "description": "No hay casos aprobados, alguno ya no coincide con el catálogo o "
            "ya hay una ejecución en curso",
        },
    },
)
def iniciar(
    historia_id: int,
    db: DbSession,
    catalogo: CatalogoActual,
    tareas: BackgroundTasks,
    sesiones: FabricaSesiones,
    runner: RunnerActual,
) -> EjecucionSalida:
    ejecucion, archivo = servicio.iniciar_ejecucion(db, historia_id, catalogo)
    respuesta = EjecucionSalida.model_validate(ejecucion)
    tareas.add_task(servicio.correr_ejecucion, ejecucion.id, archivo, sesiones, runner)
    return respuesta


@router.get(
    "/ejecuciones",
    response_model=list[EjecucionSalida],
    summary="Listar ejecuciones",
    description="Ejecuciones de la más reciente a la más antigua, con sus totales (RF-09).",
)
def listar(
    db: DbSession,
    historia_id: Annotated[int | None, Query(description="Solo las de esta historia.")] = None,
) -> list[EjecucionSalida]:
    return servicio.listar_ejecuciones(db, historia_id)


@router.get(
    "/ejecuciones/{ejecucion_id}",
    response_model=EjecucionDetalle,
    summary="Ver una ejecución",
    description="Totales, log y resultado de cada caso con su error y su captura (RF-08).",
    responses={404: {"model": ErrorDetalle, "description": "La ejecución no existe"}},
)
def detalle(ejecucion_id: int, db: DbSession) -> EjecucionDetalle:
    return servicio.obtener_ejecucion(db, ejecucion_id)


@router.get(
    "/evidencias/{resultado_id}",
    response_class=FileResponse,
    summary="Captura de un caso fallido",
    description="Captura de pantalla tomada por Playwright en el fallo (RF-08).",
    responses={
        200: {"content": {"image/png": {}}, "description": "Captura PNG"},
        404: {"model": ErrorDetalle, "description": "El resultado no tiene captura"},
    },
)
def evidencia(resultado_id: int, db: DbSession) -> FileResponse:
    return FileResponse(servicio.ruta_captura(db, resultado_id), media_type="image/png")
