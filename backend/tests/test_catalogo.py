"""Catálogo de pasos (RF-02 / CA-02): carga, reglas del archivo, arranque y API."""

import logging
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.catalogo import GRUPOS_OBLIGATORIOS, CatalogoInvalido, cargar_catalogo
from app.config import settings
from app.main import app


def _paso(id_: str, grupo: str, patron: str | None = None, plantilla: str | None = None) -> dict:
    return {
        "id": id_,
        "grupo": grupo,
        "patron": patron or f"hago {id_}",
        "plantilla": plantilla or "await page.goto('/');",
    }


def _catalogo_minimo() -> dict:
    return {
        "sut": "saucedemo",
        "base_url": "https://www.saucedemo.com",
        "version": 1,
        "pasos": [_paso(f"paso_{i}", grupo) for i, grupo in enumerate(GRUPOS_OBLIGATORIOS)],
    }


def _escribir(tmp_path: Path, datos: dict | str) -> Path:
    ruta = tmp_path / "catalogo.yaml"
    contenido = datos if isinstance(datos, str) else yaml.safe_dump(datos, allow_unicode=True)
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def _error(tmp_path: Path, datos: dict | str) -> str:
    with pytest.raises(CatalogoInvalido) as exc:
        cargar_catalogo(_escribir(tmp_path, datos))
    return str(exc.value)


# --- Catálogo real ------------------------------------------------------


def test_catalogo_real_carga_y_cubre_los_grupos_obligatorios():
    catalogo = cargar_catalogo(settings.catalogo_path)

    assert catalogo.sut == "saucedemo"
    grupos = {paso.grupo for paso in catalogo.pasos}
    assert set(GRUPOS_OBLIGATORIOS) <= grupos


def test_catalogo_real_incluye_los_pasos_del_anexo_d():
    patrones = {paso.patron for paso in cargar_catalogo(settings.catalogo_path).pasos}

    assert {
        "que estoy en la página de inicio de sesión",
        'ingreso el usuario "{texto}"',
        'ingreso la contraseña "{texto}"',
        "presiono el botón de ingresar",
        'veo el mensaje de error "{texto}"',
        "veo el listado de productos",
    } <= patrones


# --- Reglas del archivo -------------------------------------------------


def test_catalogo_minimo_valido(tmp_path):
    catalogo = cargar_catalogo(_escribir(tmp_path, _catalogo_minimo()))

    assert len(catalogo.pasos) == len(GRUPOS_OBLIGATORIOS)


def test_id_duplicado_es_invalido(tmp_path):
    datos = _catalogo_minimo()
    datos["pasos"].append(_paso("paso_0", "carrito", patron="otro patrón"))

    assert "identificador duplicado: 'paso_0'" in _error(tmp_path, datos)


def test_patron_duplicado_es_invalido(tmp_path):
    datos = _catalogo_minimo()
    datos["pasos"].append(_paso("otro", "carrito", patron="Hago paso_0"))

    assert "patrón duplicado" in _error(tmp_path, datos)


def test_falta_un_grupo_obligatorio(tmp_path):
    datos = _catalogo_minimo()
    datos["pasos"] = [p for p in datos["pasos"] if p["grupo"] != "checkout"]

    assert "faltan pasos de los grupos obligatorios: checkout" in _error(tmp_path, datos)


def test_id_con_formato_invalido(tmp_path):
    datos = _catalogo_minimo()
    datos["pasos"][0]["id"] = "Abrir Login"

    assert "pasos[0].id" in _error(tmp_path, datos)


def test_campo_faltante(tmp_path):
    datos = _catalogo_minimo()
    del datos["pasos"][1]["plantilla"]

    assert "pasos[1].plantilla" in _error(tmp_path, datos)


@pytest.mark.parametrize(
    ("patron", "plantilla", "mensaje"),
    [
        ('ingreso "{texto}"', "await page.goto('/');", "la plantilla no lo usa"),
        ("ingreso algo", "fill({texto});", "el patrón no lo tiene"),
        ("ingreso {texto}", "fill({texto});", "debe ir entre comillas"),
        ('ingreso "{valor}"', "fill({valor});", "solo admite el parámetro {texto}"),
        ('ingreso "{texto}" y "{texto}"', "fill({texto});", "como máximo un parámetro"),
    ],
)
def test_parametro_inconsistente(tmp_path, patron, plantilla, mensaje):
    datos = _catalogo_minimo()
    datos["pasos"].append(_paso("con_parametro", "carrito", patron, plantilla))

    assert mensaje in _error(tmp_path, datos)


def test_yaml_mal_formado(tmp_path):
    assert "no es YAML válido" in _error(tmp_path, "pasos: [sin cerrar")


def test_archivo_que_no_es_un_objeto(tmp_path):
    assert "debe ser un objeto" in _error(tmp_path, "- solo una lista")


def test_archivo_inexistente(tmp_path):
    with pytest.raises(CatalogoInvalido, match="No existe el archivo"):
        cargar_catalogo(tmp_path / "no_existe.yaml")


# --- Arranque del backend (CA-02) ---------------------------------------


def test_backend_no_inicia_con_catalogo_invalido(tmp_path, monkeypatch, caplog):
    datos = _catalogo_minimo()
    datos["pasos"].append(_paso("paso_0", "carrito", patron="otro patrón"))
    monkeypatch.setattr(settings, "catalogo_path", str(_escribir(tmp_path, datos)))

    with caplog.at_level(logging.ERROR), pytest.raises(CatalogoInvalido), TestClient(app):
        pass

    assert "No se pudo cargar el catálogo de pasos" in caplog.text
    assert "identificador duplicado: 'paso_0'" in caplog.text


# --- API ----------------------------------------------------------------


def test_get_catalogo(client):
    respuesta = client.get("/catalogo")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["sut"] == "saucedemo"
    assert cuerpo["version"] == 2
    primero = cuerpo["pasos"][0]
    assert primero == {
        "id": "abrir_login",
        "grupo": "inicio de sesión",
        "patron": "que estoy en la página de inicio de sesión",
        "plantilla": "await page.goto('/');",
    }
    assert len(cuerpo["pasos"]) == len(cargar_catalogo(settings.catalogo_path).pasos)
