"""Cliente HTTP único hacia el backend. Ninguna página llama a httpx ni a la base directamente."""

import os
from typing import Any

import httpx

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
API_PUBLIC_URL = os.environ.get("API_PUBLIC_URL", API_BASE_URL).rstrip("/")
TIMEOUT_SEGUNDOS = 10.0
TITULO_MAX = 120

SIN_CONEXION = "No se pudo conectar con el servidor. Probá de nuevo en unos segundos."
ERROR_INESPERADO = "El servidor respondió con un error inesperado. Probá de nuevo más tarde."
DATOS_INVALIDOS = "Los datos enviados no son válidos."

MENSAJES_CAMPO = {
    "titulo": "El título es obligatorio.",
    "descripcion": "La descripción es obligatoria.",
}
TITULO_LARGO = f"El título no puede superar los {TITULO_MAX} caracteres."


class ErrorApi(Exception):
    """Error con un mensaje en español listo para mostrar al usuario."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


def _traducir_422(cuerpo: Any) -> str:
    mensajes: list[str] = []
    errores = cuerpo.get("detail", []) if isinstance(cuerpo, dict) else []
    for error in errores:
        campo = error.get("loc", [None])[-1]
        if campo == "titulo" and error.get("type") == "string_too_long":
            mensaje = TITULO_LARGO
        else:
            mensaje = MENSAJES_CAMPO.get(campo, DATOS_INVALIDOS)
        if mensaje not in mensajes:
            mensajes.append(mensaje)
    return "  \n".join(mensajes) or DATOS_INVALIDOS


def _pedir(metodo: str, ruta: str, json: dict | None = None, aceptar: tuple = ()) -> Any:
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SEGUNDOS) as cliente:
            respuesta = cliente.request(metodo, ruta, json=json)
    except httpx.HTTPError as exc:
        raise ErrorApi(SIN_CONEXION) from exc

    if respuesta.is_success or respuesta.status_code in aceptar:
        return respuesta.json()

    try:
        cuerpo = respuesta.json()
    except ValueError:
        cuerpo = None
    if respuesta.status_code == 422:
        raise ErrorApi(_traducir_422(cuerpo))
    if isinstance(cuerpo, dict) and isinstance(cuerpo.get("detalle"), str):
        raise ErrorApi(cuerpo["detalle"])
    raise ErrorApi(ERROR_INESPERADO)


def validar_historia(datos: dict) -> list[str]:
    """Mismas reglas que el backend, para avisar sin esperar la respuesta (CA-01)."""
    errores = []
    titulo = (datos.get("titulo") or "").strip()
    if not titulo:
        errores.append(MENSAJES_CAMPO["titulo"])
    elif len(titulo) > TITULO_MAX:
        errores.append(TITULO_LARGO)
    if not (datos.get("descripcion") or "").strip():
        errores.append(MENSAJES_CAMPO["descripcion"])
    return errores


def _validar_o_fallar(datos: dict) -> None:
    errores = validar_historia(datos)
    if errores:
        raise ErrorApi("  \n".join(errores))


def listar_historias() -> list[dict]:
    return _pedir("GET", "/historias")


def obtener_historia(historia_id: int) -> dict:
    return _pedir("GET", f"/historias/{historia_id}")


def crear_historia(datos: dict) -> dict:
    _validar_o_fallar(datos)
    return _pedir("POST", "/historias", json=datos)


def editar_historia(historia_id: int, datos: dict) -> dict:
    _validar_o_fallar(datos)
    return _pedir("PUT", f"/historias/{historia_id}", json=datos)


def salud() -> dict:
    # 503 trae el cuerpo con estado "degradado": se devuelve igual para mostrarlo.
    return _pedir("GET", "/salud", aceptar=(503,))
