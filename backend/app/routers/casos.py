from fastapi import APIRouter, status

from app.catalogo import CatalogoActual
from app.db import DbSession
from app.schemas.casos import CasoSalida, GeneracionSalida
from app.schemas.errores import ErrorDetalle
from app.services import casos as servicio_casos
from app.services import generaciones as servicio_generaciones
from app.services.llm import Proveedor

router = APIRouter(prefix="/historias/{historia_id}", tags=["Casos"])


@router.post(
    "/generaciones",
    response_model=GeneracionSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Generar casos con IA",
    description=(
        "Pide al LLM entre 3 y 8 casos Gherkin para la historia y los valida contra el catálogo "
        "(RF-03, RF-04). Si la respuesta no respeta el formato, reintenta hasta 2 veces. Los "
        "casos quedan pendientes y los inválidos se marcan con sus errores. Al regenerar, los "
        "casos pendientes anteriores se reemplazan y los aprobados se conservan (RF-11). Toda "
        "generación queda registrada, también las fallidas."
    ),
    responses={
        404: {"model": ErrorDetalle, "description": "La historia no existe"},
        429: {"model": ErrorDetalle, "description": "Se alcanzó el límite diario (RNF-08)"},
        502: {"model": ErrorDetalle, "description": "El LLM falló o no respetó el formato"},
        503: {"model": ErrorDetalle, "description": "El LLM no está configurado"},
    },
)
def generar(
    historia_id: int, db: DbSession, proveedor: Proveedor, catalogo: CatalogoActual
) -> GeneracionSalida:
    return servicio_generaciones.generar_casos(db, historia_id, proveedor, catalogo)


@router.get(
    "/casos",
    response_model=list[CasoSalida],
    summary="Listar casos de una historia",
    description="Devuelve los casos de la historia en orden de creación, con su validación.",
    responses={404: {"model": ErrorDetalle, "description": "La historia no existe"}},
)
def listar(historia_id: int, db: DbSession) -> list[CasoSalida]:
    return servicio_casos.listar_casos(db, historia_id)
