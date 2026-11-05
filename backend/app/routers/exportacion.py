from fastapi import APIRouter
from fastapi.responses import Response

from app.catalogo import CatalogoActual
from app.db import DbSession
from app.schemas.errores import ErrorDetalle
from app.services import exportador

router = APIRouter(tags=["Exportación"])


@router.get(
    "/historias/{historia_id}/export",
    summary="Exportar a Playwright",
    description=(
        "Descarga `HU-n.spec.ts` con los casos aprobados de la historia: un `test.describe` "
        "por historia, un `test` por caso con su código `[CP-n]` y un `test.step` por paso "
        "Gherkin (RF-06). El código sale de las plantillas del catálogo y los valores se "
        "escapan como literales de cadena (RNF-05)."
    ),
    response_class=Response,
    responses={
        200: {
            "content": {"text/plain": {}},
            "description": "Archivo .spec.ts para descargar",
        },
        404: {"model": ErrorDetalle, "description": "La historia no existe"},
        409: {
            "model": ErrorDetalle,
            "description": "No hay casos aprobados o alguno ya no coincide con el catálogo",
        },
    },
)
def exportar(historia_id: int, db: DbSession, catalogo: CatalogoActual) -> Response:
    archivo = exportador.exportar_historia(db, historia_id, catalogo)
    return Response(
        content=archivo.contenido,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{archivo.nombre}"'},
    )
