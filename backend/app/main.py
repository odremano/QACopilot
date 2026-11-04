import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.catalogo import CatalogoInvalido, cargar_catalogo
from app.config import settings
from app.errors import registrar_manejadores
from app.routers import catalogo, historias, salud
from app.version import VERSION

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Sin un catálogo válido no hay generación ni exportación posibles: el backend no inicia.
    try:
        app.state.catalogo = cargar_catalogo(settings.catalogo_path)
    except CatalogoInvalido as exc:
        logger.error("No se pudo cargar el catálogo de pasos. %s", exc)
        raise
    logger.info(
        "Catálogo '%s' v%s cargado con %d pasos",
        app.state.catalogo.sut,
        app.state.catalogo.version,
        len(app.state.catalogo.pasos),
    )
    yield


app = FastAPI(
    title="QA Copilot API",
    description=(
        "API de QA Copilot: generación asistida por IA de casos de prueba Gherkin y scripts "
        "de Playwright a partir de historias de usuario. "
        "**La IA propone, el sistema valida y la persona decide.**"
    ),
    version=VERSION,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Historias", "description": "Gestión de historias de usuario (RF-01)."},
        {"name": "Catálogo", "description": "Pasos Gherkin permitidos para el SUT (RF-02)."},
        {"name": "Salud", "description": "Estado del servicio y de sus dependencias."},
    ],
)

registrar_manejadores(app)
app.include_router(historias.router)
app.include_router(catalogo.router)
app.include_router(salud.router)
