from fastapi import APIRouter, status

from app.catalogo import CatalogoActual
from app.db import DbSession
from app.schemas.casos import CasoEdicion, CasoSalida, GeneracionSalida
from app.schemas.errores import ErrorDetalle
from app.services import casos as servicio_casos
from app.services import generaciones as servicio_generaciones
from app.services.llm import Proveedor

router = APIRouter(tags=["Casos"])

HISTORIA_NO_ENCONTRADA = {404: {"model": ErrorDetalle, "description": "La historia no existe"}}
CASO_NO_ENCONTRADO = {404: {"model": ErrorDetalle, "description": "El caso no existe"}}
TRANSICION_INVALIDA = {
    409: {"model": ErrorDetalle, "description": "El estado actual no permite la acción"}
}


@router.post(
    "/historias/{historia_id}/generaciones",
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
        **HISTORIA_NO_ENCONTRADA,
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
    "/historias/{historia_id}/casos",
    response_model=list[CasoSalida],
    summary="Listar casos de una historia",
    description="Devuelve los casos de la historia en orden de creación, con su validación.",
    responses=HISTORIA_NO_ENCONTRADA,
)
def listar(historia_id: int, db: DbSession) -> list[CasoSalida]:
    return servicio_casos.listar_casos(db, historia_id)


@router.put(
    "/casos/{caso_id}",
    response_model=CasoSalida,
    summary="Editar un caso",
    description=(
        "Reemplaza el Gherkin de un caso pendiente y lo revalida contra el catálogo (RF-05, "
        "RF-04). El caso se guarda aunque quede inválido, con el detalle de sus errores. Si "
        "queda válido, el título se toma de la línea «Escenario:»."
    ),
    responses={**CASO_NO_ENCONTRADO, **TRANSICION_INVALIDA},
)
def editar(caso_id: int, datos: CasoEdicion, db: DbSession, catalogo: CatalogoActual) -> CasoSalida:
    return servicio_casos.editar_caso(db, caso_id, datos.gherkin, catalogo)


@router.post(
    "/casos/{caso_id}/aprobar",
    response_model=CasoSalida,
    summary="Aprobar un caso",
    description="Pasa un caso pendiente y válido a «aprobado» (RF-05).",
    responses={**CASO_NO_ENCONTRADO, **TRANSICION_INVALIDA},
)
def aprobar(caso_id: int, db: DbSession) -> CasoSalida:
    return servicio_casos.cambiar_estado(db, caso_id, "aprobar")


@router.post(
    "/casos/{caso_id}/descartar",
    response_model=CasoSalida,
    summary="Descartar un caso",
    description="Pasa un caso pendiente a «descartado»: no se exporta ni se ejecuta (RF-05).",
    responses={**CASO_NO_ENCONTRADO, **TRANSICION_INVALIDA},
)
def descartar(caso_id: int, db: DbSession) -> CasoSalida:
    return servicio_casos.cambiar_estado(db, caso_id, "descartar")


@router.post(
    "/casos/{caso_id}/pendiente",
    response_model=CasoSalida,
    summary="Volver un caso a pendiente",
    description="Devuelve un caso aprobado o descartado a «pendiente» para editarlo (RF-05).",
    responses={**CASO_NO_ENCONTRADO, **TRANSICION_INVALIDA},
)
def volver_a_pendiente(caso_id: int, db: DbSession) -> CasoSalida:
    return servicio_casos.cambiar_estado(db, caso_id, "pendiente")
