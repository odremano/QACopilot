"""Proveedores del LLM (RF-03, RF-10). Todos devuelven el texto crudo de la respuesta.

- openrouter / deepseek: API compatible con OpenAI (chat/completions) con salida JSON.
- demo: respuestas pregrabadas en `demo/`, sin llamar a la red (RF-10).

La clave solo se usa en el encabezado Authorization: nunca se registra ni se devuelve.
"""

import logging
import re
import unicodedata
from typing import Annotated, Protocol

import httpx
from fastapi import Depends

from app.catalogo import RAIZ_BACKEND
from app.config import settings
from app.errors import ErrorNegocio
from app.models import HistoriaUsuario

logger = logging.getLogger(__name__)

PROVEEDORES_COMPATIBLES = ("openrouter", "deepseek")
PROVEEDOR_DEMO = "demo"
RUTA_DEMO = RAIZ_BACKEND / "demo"

TIMEOUT_SEGUNDOS = 90.0
# Holgado: los modelos que razonan gastan parte del presupuesto antes de responder.
MAX_TOKENS = 8000
TEMPERATURA = 0.2

ERRORES_HTTP = {
    401: "El proveedor del LLM rechazó la clave configurada (LLM_API_KEY).",
    402: "La cuenta del proveedor del LLM no tiene crédito suficiente.",
    403: "El proveedor del LLM rechazó la solicitud.",
    404: "El proveedor del LLM no reconoce el modelo configurado (LLM_MODEL).",
    429: "El proveedor del LLM está limitando las solicitudes. Probá de nuevo en un rato.",
}
NO_RESPONDE = "El proveedor del LLM no respondió a tiempo. Probá de nuevo en unos minutos."
ERROR_PROVEEDOR = "El proveedor del LLM respondió con un error. Probá de nuevo en unos minutos."


class ErrorProveedor(Exception):
    """Falla del proveedor (red, autenticación, crédito). No se reintenta."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ProveedorLLM(Protocol):
    nombre: str
    modelo: str

    def completar(self, mensajes: list[dict[str, str]], historia: HistoriaUsuario) -> str: ...


class ProveedorCompatibleOpenAI:
    def __init__(
        self,
        nombre: str,
        base_url: str,
        modelo: str,
        api_key: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.nombre = nombre
        self.modelo = modelo
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._transport = transport

    def completar(self, mensajes: list[dict[str, str]], historia: HistoriaUsuario) -> str:
        cuerpo: dict = {
            "model": self.modelo,
            "messages": mensajes,
            "response_format": {"type": "json_object"},
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURA,
        }
        if self.nombre == "openrouter":
            # No devolver el razonamiento: solo se usa la respuesta final.
            cuerpo["reasoning"] = {"exclude": True}
        try:
            with httpx.Client(timeout=TIMEOUT_SEGUNDOS, transport=self._transport) as cliente:
                respuesta = cliente.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=cuerpo,
                )
        except httpx.TimeoutException as exc:
            raise ErrorProveedor(NO_RESPONDE) from exc
        except httpx.HTTPError as exc:
            logger.warning("No se pudo contactar al proveedor del LLM: %s", exc)
            raise ErrorProveedor(NO_RESPONDE) from exc

        if not respuesta.is_success:
            logger.warning(
                "El proveedor del LLM respondió %s: %s",
                respuesta.status_code,
                respuesta.text[:500],
            )
            raise ErrorProveedor(ERRORES_HTTP.get(respuesta.status_code, ERROR_PROVEEDOR))
        try:
            contenido = respuesta.json()["choices"][0]["message"].get("content")
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ErrorProveedor(ERROR_PROVEEDOR) from exc
        # Contenido vacío o nulo: lo trata el validador como respuesta vacía (se reintenta).
        return contenido or ""


class ProveedorDemo:
    """Respuestas pregrabadas para las historias de ejemplo, elegidas por el título."""

    nombre = PROVEEDOR_DEMO
    modelo = "respuestas-pregrabadas"

    def completar(self, mensajes: list[dict[str, str]], historia: HistoriaUsuario) -> str:
        ruta = RUTA_DEMO / f"{nombre_archivo_demo(historia.titulo)}.json"
        if not ruta.is_file():
            raise ErrorProveedor(
                "El modo demo solo tiene respuestas para las historias de ejemplo "
                "(Inicio de sesión, Carrito de compras y Checkout)."
            )
        return ruta.read_text(encoding="utf-8")


def nombre_archivo_demo(titulo: str) -> str:
    """'Carrito de compras' → 'carrito-de-compras'."""
    sin_tildes = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sin_tildes.casefold()).strip("-")


def obtener_proveedor() -> ProveedorLLM:
    """Dependencia de FastAPI: el proveedor según la configuración (las pruebas la reemplazan)."""
    if settings.llm_provider == PROVEEDOR_DEMO:
        return ProveedorDemo()
    if settings.llm_provider not in PROVEEDORES_COMPATIBLES:
        raise ErrorNegocio(
            f"LLM_PROVIDER='{settings.llm_provider}' no es válido. Valores posibles: "
            f"{', '.join((*PROVEEDORES_COMPATIBLES, PROVEEDOR_DEMO))}.",
            status_code=503,
        )
    if not settings.llm_configurado:
        raise ErrorNegocio(
            "La generación con IA no está disponible: falta configurar LLM_API_KEY.",
            status_code=503,
        )
    return ProveedorCompatibleOpenAI(
        nombre=settings.llm_provider,
        base_url=settings.llm_base_url,
        modelo=settings.llm_model,
        api_key=settings.llm_api_key.get_secret_value(),
    )


Proveedor = Annotated[ProveedorLLM, Depends(obtener_proveedor)]
