"""Cliente HTTP único hacia el backend. Ninguna página llama a httpx ni a la base directamente."""

import os
import re
from typing import Any

import httpx

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
API_PUBLIC_URL = os.environ.get("API_PUBLIC_URL", API_BASE_URL).rstrip("/")
TIMEOUT_SEGUNDOS = 10.0
# La generación puede reintentar hasta 3 veces contra el LLM (90 s cada una como máximo).
TIMEOUT_GENERACION = 300.0
TITULO_MAX = 120

SIN_CONEXION = "No se pudo conectar con el servidor. Probá de nuevo en unos segundos."
ERROR_INESPERADO = "El servidor respondió con un error inesperado. Probá de nuevo más tarde."
DATOS_INVALIDOS = "Los datos enviados no son válidos."

MENSAJES_CAMPO = {
    "titulo": "El título es obligatorio.",
    "descripcion": "La descripción es obligatoria.",
    "gherkin": "El Gherkin del caso no puede estar vacío.",
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


def _pedir(
    metodo: str,
    ruta: str,
    json: dict | None = None,
    aceptar: tuple = (),
    timeout: float = TIMEOUT_SEGUNDOS,
) -> Any:
    return _enviar(metodo, ruta, json=json, aceptar=aceptar, timeout=timeout).json()


def _enviar(
    metodo: str,
    ruta: str,
    json: dict | None = None,
    aceptar: tuple = (),
    timeout: float = TIMEOUT_SEGUNDOS,
) -> httpx.Response:
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=timeout) as cliente:
            respuesta = cliente.request(metodo, ruta, json=json)
    except httpx.HTTPError as exc:
        raise ErrorApi(SIN_CONEXION) from exc

    if respuesta.is_success or respuesta.status_code in aceptar:
        return respuesta

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


def listar_casos(historia_id: int) -> list[dict]:
    return _pedir("GET", f"/historias/{historia_id}/casos")


def generar_casos(historia_id: int) -> dict:
    """Genera (o regenera) casos con IA. Puede tardar: usa un timeout largo."""
    return _pedir("POST", f"/historias/{historia_id}/generaciones", timeout=TIMEOUT_GENERACION)


def editar_caso(caso_id: int, gherkin: str) -> dict:
    """Guarda el Gherkin de un caso pendiente; el backend lo revalida (RF-05)."""
    if not gherkin.strip():
        raise ErrorApi(MENSAJES_CAMPO["gherkin"])
    return _pedir("PUT", f"/casos/{caso_id}", json={"gherkin": gherkin})


def aprobar_caso(caso_id: int) -> dict:
    return _pedir("POST", f"/casos/{caso_id}/aprobar")


def descartar_caso(caso_id: int) -> dict:
    return _pedir("POST", f"/casos/{caso_id}/descartar")


def volver_a_pendiente(caso_id: int) -> dict:
    return _pedir("POST", f"/casos/{caso_id}/pendiente")


def exportar_spec(historia_id: int) -> tuple[str, str]:
    """Nombre y contenido del .spec.ts con los casos aprobados de la historia (RF-06)."""
    respuesta = _enviar("GET", f"/historias/{historia_id}/export")
    nombre = re.search(r'filename="([^"]+)"', respuesta.headers.get("content-disposition", ""))
    return (nombre.group(1) if nombre else f"HU-{historia_id}.spec.ts"), respuesta.text


def obtener_catalogo() -> dict:
    return _pedir("GET", "/catalogo")


def salud() -> dict:
    # 503 trae el cuerpo con estado "degradado": se devuelve igual para mostrarlo.
    return _pedir("GET", "/salud", aceptar=(503,))
