import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.config import settings
from app.db import DbSession
from app.schemas.salud import EstadoLlm, Salud
from app.version import VERSION

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Salud"])


@router.get(
    "/salud",
    response_model=Salud,
    summary="Estado del servicio",
    description=(
        "Informa el estado de la API, la conexión con la base de datos y la configuración "
        "del LLM. Nunca expone la clave del proveedor. Devuelve 503 si la base no responde."
    ),
    responses={503: {"model": Salud, "description": "Base de datos no disponible"}},
)
def salud(response: Response, db: DbSession) -> Salud:
    try:
        db.execute(text("SELECT 1"))
        base_de_datos = "ok"
    except Exception:
        logger.exception("La base de datos no responde")
        base_de_datos = "error"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return Salud(
        estado="ok" if base_de_datos == "ok" else "degradado",
        base_de_datos=base_de_datos,
        llm=EstadoLlm(
            proveedor=settings.llm_provider,
            modelo=settings.llm_model,
            configurado=settings.llm_configurado,
        ),
        version=VERSION,
    )
