import logging

from fastapi import FastAPI

from app.config import settings
from app.errors import registrar_manejadores
from app.routers import historias, salud
from app.version import VERSION

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="QA Copilot API",
    description=(
        "API de QA Copilot: generación asistida por IA de casos de prueba Gherkin y scripts "
        "de Playwright a partir de historias de usuario. "
        "**La IA propone, el sistema valida y la persona decide.**"
    ),
    version=VERSION,
    openapi_tags=[
        {"name": "Historias", "description": "Gestión de historias de usuario (RF-01)."},
        {"name": "Salud", "description": "Estado del servicio y de sus dependencias."},
    ],
)

registrar_manejadores(app)
app.include_router(historias.router)
app.include_router(salud.router)
