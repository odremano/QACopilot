from fastapi import APIRouter

from app.catalogo import CatalogoActual
from app.schemas.catalogo import CatalogoSalida

router = APIRouter(prefix="/catalogo", tags=["Catálogo"])


@router.get(
    "",
    response_model=CatalogoSalida,
    summary="Obtener el catálogo de pasos",
    description=(
        "Devuelve los pasos Gherkin permitidos para el SUT, en el orden del archivo, cada uno "
        "con su grupo, su patrón y la plantilla de Playwright que se usa al exportar."
    ),
)
def obtener(catalogo: CatalogoActual) -> CatalogoSalida:
    return CatalogoSalida.model_validate(catalogo)
