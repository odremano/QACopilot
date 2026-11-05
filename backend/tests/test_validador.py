"""Validador de casos (RF-04 / CA-04): esquema JSON, sintaxis Gherkin y pasos del catálogo."""

import json

import pytest

from app.catalogo import cargar_catalogo
from app.config import settings
from app.models.estados import TipoCaso
from app.services.validador import RespuestaInvalida, validar_gherkin, validar_respuesta

CATALOGO = cargar_catalogo(settings.catalogo_path)

LOGIN_VALIDO = """\
Escenario: Inicio de sesión exitoso
  Dado que estoy en la página de inicio de sesión
  Cuando ingreso el usuario "standard_user"
  Y ingreso la contraseña "secret_sauce"
  Y presiono el botón de ingresar
  Entonces veo el listado de productos
"""

LOGIN_SIN_USUARIO = """\
Escenario: Usuario vacío
  Dado que estoy en la página de inicio de sesión
  Cuando ingreso el usuario ""
  Y presiono el botón de ingresar
  Entonces veo el mensaje de error "Epic sadface: Username is required"
"""


def _respuesta(*casos: dict) -> str:
    return json.dumps({"casos": list(casos)}, ensure_ascii=False)


def _caso(gherkin: str = LOGIN_VALIDO, tipo: str = "positivo", titulo: str = "Login") -> dict:
    return {"titulo": titulo, "tipo": tipo, "gherkin": gherkin}


# --- Coincidencia con el catálogo ------------------------------------------


def test_coincidir_devuelve_el_paso_y_el_valor_del_parametro():
    coincidencia = CATALOGO.coincidir('ingreso el usuario "standard_user"')

    assert coincidencia is not None
    assert coincidencia.paso.id == "ingresar_usuario"
    assert coincidencia.valor == "standard_user"


def test_coincidir_paso_sin_parametro():
    coincidencia = CATALOGO.coincidir("presiono el botón de ingresar")

    assert coincidencia is not None
    assert coincidencia.valor is None


def test_coincidir_ignora_mayusculas_y_espacios_pero_conserva_el_valor():
    coincidencia = CATALOGO.coincidir('  Ingreso   el USUARIO "Locked_Out_User" ')

    assert coincidencia is not None
    assert coincidencia.valor == "Locked_Out_User"


def test_coincidir_acepta_un_valor_vacio():
    coincidencia = CATALOGO.coincidir('ingreso el usuario ""')

    assert coincidencia is not None
    assert coincidencia.valor == ""


@pytest.mark.parametrize(
    "texto",
    [
        "presiono el botón comprar",  # no existe
        "ingreso el usuario standard_user",  # sin comillas
        "presiono el botón de ingresar ya",  # texto de más
        'veo el mensaje de error "a" "b"',  # comillas sobrantes
    ],
)
def test_coincidir_rechaza_pasos_fuera_del_catalogo(texto):
    assert CATALOGO.coincidir(texto) is None


# --- validar_gherkin -------------------------------------------------------


def test_caso_valido_no_tiene_errores():
    assert validar_gherkin(LOGIN_VALIDO, CATALOGO) == []


def test_caso_con_valor_vacio_es_valido():
    assert validar_gherkin(LOGIN_SIN_USUARIO, CATALOGO) == []


def test_paso_fuera_del_catalogo_se_senala():
    gherkin = LOGIN_VALIDO.replace("presiono el botón de ingresar", "hago clic en Login")

    assert validar_gherkin(gherkin, CATALOGO) == [
        "Paso 4: «Y hago clic en Login» no coincide con ningún paso del catálogo."
    ]


def test_se_informan_todos_los_pasos_invalidos():
    gherkin = (
        "Escenario: x\n  Dado algo raro\n  Cuando otra cosa\n  Entonces veo el listado de productos"
    )

    errores = validar_gherkin(gherkin, CATALOGO)

    assert [e.split(":")[0] for e in errores] == ["Paso 1", "Paso 2"]


def test_linea_que_no_es_gherkin_indica_la_linea_del_caso():
    gherkin = LOGIN_VALIDO + "  esto no es un paso\n"

    assert validar_gherkin(gherkin, CATALOGO) == [
        "Línea 7: «esto no es un paso» no es una línea Gherkin válida."
    ]


def test_palabras_clave_en_ingles_son_invalidas():
    gherkin = "Scenario: Login\n  Given que estoy en la página de inicio de sesión"

    errores = validar_gherkin(gherkin, CATALOGO)

    assert errores[0].startswith("Hay texto antes del escenario: «Scenario: Login»")


def test_texto_libre_dentro_del_escenario_es_invalido():
    gherkin = LOGIN_VALIDO.replace("  Dado que", "  Primero abro el sitio\n  Dado que")

    assert validar_gherkin(gherkin, CATALOGO) == [
        "Hay texto que no es un paso: «Primero abro el sitio». "
        "Los pasos empiezan con Dado, Cuando, Entonces, Y o Pero."
    ]


def test_bloque_de_texto_sin_cerrar():
    gherkin = LOGIN_VALIDO + '  """\n  abierto\n'

    assert "termina de forma incompleta" in validar_gherkin(gherkin, CATALOGO)[0]


@pytest.mark.parametrize(
    ("gherkin", "mensaje"),
    [
        ("", "no tiene contenido Gherkin"),
        ("Característica: Login\n" + LOGIN_VALIDO, "sin la línea «Característica:»"),
        ("# solo un comentario", "no tiene un «Escenario:»"),
        ("Escenario: vacío\n", "no tiene pasos"),
        (LOGIN_VALIDO + LOGIN_SIN_USUARIO, "tiene 2 escenarios"),
        (
            "Antecedentes:\n  Dado que estoy en la página de inicio de sesión\n" + LOGIN_VALIDO,
            "no admite «Antecedentes»",
        ),
    ],
)
def test_estructura_invalida(gherkin, mensaje):
    assert any(mensaje in error for error in validar_gherkin(gherkin, CATALOGO))


def test_esquema_del_escenario_no_se_admite():
    gherkin = (
        "Esquema del escenario: Login\n"
        "  Dado que estoy en la página de inicio de sesión\n"
        '  Cuando ingreso el usuario "<usuario>"\n'
        "Ejemplos:\n"
        "  | usuario |\n"
        "  | standard_user |\n"
    )

    assert any("Esquema del escenario" in e for e in validar_gherkin(gherkin, CATALOGO))


def test_tabla_en_un_paso_no_se_admite():
    gherkin = LOGIN_VALIDO + "    | a | b |\n"

    assert validar_gherkin(gherkin, CATALOGO) == [
        "Paso 5 («Entonces veo el listado de productos»): no se admiten tablas ni bloques de texto."
    ]


# --- validar_respuesta (respuesta del LLM) ---------------------------------


def test_respuesta_valida_con_casos_validos_e_invalidos():
    invalido = LOGIN_VALIDO.replace("veo el listado de productos", "veo la tienda")
    contenido = _respuesta(
        _caso(),
        _caso(LOGIN_SIN_USUARIO, tipo="negativo", titulo="Sin usuario"),
        _caso(invalido, tipo="limite"),
    )

    casos = validar_respuesta(contenido, CATALOGO)

    assert [c.tipo for c in casos] == [TipoCaso.POSITIVO, TipoCaso.NEGATIVO, TipoCaso.LIMITE]
    assert [c.valido for c in casos] == [True, True, False]
    assert casos[1].titulo == "Sin usuario"
    assert "no coincide con ningún paso del catálogo" in casos[2].errores[0]


@pytest.mark.parametrize("tipo", ["Positivo", " NEGATIVO ", "límite"])
def test_tipo_se_normaliza(tipo):
    assert validar_respuesta(_respuesta(_caso(tipo=tipo)), CATALOGO)[0].valido


@pytest.mark.parametrize(
    ("contenido", "mensaje"),
    [
        ("", "respuesta vacía"),
        ("   ", "respuesta vacía"),
        ("Aquí tenés los casos: ...", "no es JSON válido"),
        ('{"casos": [', "no es JSON válido"),
        ('{"casos": []}', "no propuso ningún caso"),
        ('{"escenarios": []}', "no respeta el formato"),
        (_respuesta(_caso(tipo="feliz")), "no respeta el formato"),
        (_respuesta({"titulo": "x", "tipo": "positivo"}), "no respeta el formato"),
        (_respuesta(_caso(titulo="x" * 201)), "no respeta el formato"),
    ],
)
def test_respuesta_invalida_lanza_excepcion_para_reintentar(contenido, mensaje):
    with pytest.raises(RespuestaInvalida) as exc:
        validar_respuesta(contenido, CATALOGO)

    assert mensaje in exc.value.mensaje


def test_respuesta_invalida_conserva_el_detalle_tecnico():
    with pytest.raises(RespuestaInvalida) as exc:
        validar_respuesta(_respuesta(_caso(tipo="feliz")), CATALOGO)

    assert exc.value.detalle is not None
    assert "casos[0].tipo" in exc.value.detalle
