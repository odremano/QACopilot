from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorNegocio(Exception):
    """Error esperado de la lógica de negocio, con mensaje en español para el usuario."""

    def __init__(self, detalle: str, status_code: int = 400) -> None:
        super().__init__(detalle)
        self.detalle = detalle
        self.status_code = status_code


class NoEncontrado(ErrorNegocio):
    def __init__(self, detalle: str) -> None:
        super().__init__(detalle, status_code=404)


def registrar_manejadores(app: FastAPI) -> None:
    """Respuestas de error con forma {"detalle": "..."} (los 422 de Pydantic quedan estándar)."""

    @app.exception_handler(ErrorNegocio)
    async def manejar_error_negocio(_: Request, exc: ErrorNegocio) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detalle": exc.detalle})

    @app.exception_handler(StarletteHTTPException)
    async def manejar_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detalle = exc.detail
        if exc.status_code == 404 and detalle == "Not Found":
            detalle = "El recurso solicitado no existe"
        return JSONResponse(
            status_code=exc.status_code, content={"detalle": detalle}, headers=exc.headers
        )
