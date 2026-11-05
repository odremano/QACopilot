"""Proveedor compatible con OpenAI (OpenRouter / DeepSeek) contra un transporte simulado."""

import json

import httpx
import pytest

from app.models import HistoriaUsuario
from app.services.llm import ErrorProveedor, ProveedorCompatibleOpenAI, nombre_archivo_demo

MENSAJES = [{"role": "system", "content": "json"}, {"role": "user", "content": "historia"}]
HISTORIA = HistoriaUsuario(titulo="x", descripcion="y")


def _proveedor(manejador, nombre: str = "openrouter") -> ProveedorCompatibleOpenAI:
    return ProveedorCompatibleOpenAI(
        nombre=nombre,
        base_url="https://llm.ejemplo/api/v1/",
        modelo="deepseek/modelo",
        api_key="clave-secreta",
        transport=httpx.MockTransport(manejador),
    )


def _ok(contenido: str | None) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": contenido}}]})


def test_envia_el_pedido_con_salida_json_y_devuelve_el_contenido():
    pedidos: list[httpx.Request] = []

    def manejador(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return _ok('{"casos": []}')

    assert _proveedor(manejador).completar(MENSAJES, HISTORIA) == '{"casos": []}'

    (pedido,) = pedidos
    assert str(pedido.url) == "https://llm.ejemplo/api/v1/chat/completions"
    assert pedido.headers["authorization"] == "Bearer clave-secreta"
    cuerpo = json.loads(pedido.content)
    assert cuerpo["model"] == "deepseek/modelo"
    assert cuerpo["messages"] == MENSAJES
    assert cuerpo["response_format"] == {"type": "json_object"}
    assert cuerpo["max_tokens"] > 0
    assert cuerpo["reasoning"] == {"exclude": True}


def test_deepseek_directo_no_envia_parametros_de_openrouter():
    pedidos: list[httpx.Request] = []

    def manejador(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return _ok("{}")

    _proveedor(manejador, nombre="deepseek").completar(MENSAJES, HISTORIA)

    assert "reasoning" not in json.loads(pedidos[0].content)


def test_contenido_nulo_se_devuelve_vacio_para_reintentar():
    assert _proveedor(lambda _: _ok(None)).completar(MENSAJES, HISTORIA) == ""


@pytest.mark.parametrize(
    ("codigo", "mensaje"),
    [
        (401, "rechazó la clave configurada"),
        (402, "no tiene crédito suficiente"),
        (404, "no reconoce el modelo configurado"),
        (429, "está limitando las solicitudes"),
        (500, "respondió con un error"),
    ],
)
def test_errores_http_se_traducen(codigo, mensaje):
    proveedor = _proveedor(lambda _: httpx.Response(codigo, json={"error": "x"}))

    with pytest.raises(ErrorProveedor, match=mensaje):
        proveedor.completar(MENSAJES, HISTORIA)


def test_timeout_se_informa():
    def manejador(pedido: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("lento", request=pedido)

    with pytest.raises(ErrorProveedor, match="no respondió a tiempo"):
        _proveedor(manejador).completar(MENSAJES, HISTORIA)


def test_respuesta_sin_choices_es_error_del_proveedor():
    proveedor = _proveedor(lambda _: httpx.Response(200, json={"error": "raro"}))

    with pytest.raises(ErrorProveedor, match="respondió con un error"):
        proveedor.completar(MENSAJES, HISTORIA)


@pytest.mark.parametrize(
    ("titulo", "archivo"),
    [
        ("Inicio de sesión", "inicio-de-sesion"),
        ("Carrito de compras", "carrito-de-compras"),
        ("  Checkout ", "checkout"),
    ],
)
def test_nombre_archivo_demo(titulo, archivo):
    assert nombre_archivo_demo(titulo) == archivo
