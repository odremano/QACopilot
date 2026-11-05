"""Revisión humana de casos (RF-05 / CA-05): aprobar, descartar, volver a pendiente y editar."""

import pytest

from app.models import CasoPrueba, HistoriaUsuario
from app.models.estados import EstadoCaso, TipoCaso

VALIDO = """\
Escenario: Ingreso exitoso
  Dado que estoy en la página de inicio de sesión
  Cuando ingreso el usuario "standard_user"
  Y ingreso la contraseña "secret_sauce"
  Y presiono el botón de ingresar
  Entonces veo el listado de productos
"""
INVALIDO = VALIDO.replace("presiono el botón de ingresar", "hago clic en Login")
ERROR_INVALIDO = "Paso 4: «Y hago clic en Login» no coincide con ningún paso del catálogo."


@pytest.fixture
def crear_caso(db):
    historia = HistoriaUsuario(titulo="Login", descripcion="Como cliente quiero ingresar.")
    db.add(historia)
    db.commit()

    def crear(estado: EstadoCaso = EstadoCaso.PENDIENTE, valido: bool = True) -> int:
        caso = CasoPrueba(
            historia_id=historia.id,
            titulo="Ingreso exitoso",
            tipo=TipoCaso.POSITIVO,
            gherkin=VALIDO if valido else INVALIDO,
            estado=estado,
            valido=valido,
            errores_validacion=None if valido else [ERROR_INVALIDO],
        )
        db.add(caso)
        db.commit()
        return caso.id

    return crear


def _accion(client, caso_id: int, accion: str):
    return client.post(f"/casos/{caso_id}/{accion}")


# --- CA-05 -----------------------------------------------------------------


def test_aprobar_un_caso_valido(client, crear_caso):
    caso_id = crear_caso()

    respuesta = _accion(client, caso_id, "aprobar")

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "aprobado"
    assert client.get("/historias/1").json()["resumen_casos"]["aprobado"] == 1


def test_no_se_puede_aprobar_un_caso_invalido(client, crear_caso):
    caso_id = crear_caso(valido=False)

    respuesta = _accion(client, caso_id, "aprobar")

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detalle": "Solo se aprueban casos válidos: corregí CP-1 antes de aprobarlo."
    }
    assert client.get("/historias/1/casos").json()[0]["estado"] == "pendiente"


def test_editar_y_revalidar_un_caso_invalido(client, crear_caso):
    caso_id = crear_caso(valido=False)

    respuesta = client.put(f"/casos/{caso_id}", json={"gherkin": VALIDO})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["valido"] is True
    assert cuerpo["errores_validacion"] == []
    assert cuerpo["gherkin"] == VALIDO
    assert _accion(client, caso_id, "aprobar").status_code == 200


def test_descartar_un_caso(client, crear_caso):
    caso_id = crear_caso()

    respuesta = _accion(client, caso_id, "descartar")

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "descartado"


# --- Máquina de estados ----------------------------------------------------


@pytest.mark.parametrize(
    ("estado", "accion", "esperado"),
    [
        (EstadoCaso.PENDIENTE, "aprobar", "aprobado"),
        (EstadoCaso.PENDIENTE, "descartar", "descartado"),
        (EstadoCaso.APROBADO, "pendiente", "pendiente"),
        (EstadoCaso.DESCARTADO, "pendiente", "pendiente"),
    ],
)
def test_transiciones_permitidas(client, crear_caso, estado, accion, esperado):
    caso_id = crear_caso(estado)

    respuesta = _accion(client, caso_id, accion)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == esperado


@pytest.mark.parametrize(
    ("estado", "accion", "mensaje"),
    [
        (
            EstadoCaso.APROBADO,
            "aprobar",
            "Solo se pueden aprobar casos pendientes: CP-1 está aprobado.",
        ),
        (
            EstadoCaso.DESCARTADO,
            "aprobar",
            "Solo se pueden aprobar casos pendientes: CP-1 está descartado.",
        ),
        (
            EstadoCaso.APROBADO,
            "descartar",
            "Solo se pueden descartar casos pendientes: CP-1 está aprobado.",
        ),
        (
            EstadoCaso.DESCARTADO,
            "descartar",
            "Solo se pueden descartar casos pendientes: CP-1 está descartado.",
        ),
        (EstadoCaso.PENDIENTE, "pendiente", "CP-1 ya está pendiente."),
    ],
)
def test_transiciones_invalidas(client, crear_caso, estado, accion, mensaje):
    caso_id = crear_caso(estado)

    respuesta = _accion(client, caso_id, accion)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detalle": mensaje}


def test_un_caso_descartado_vuelve_a_pendiente_y_se_puede_aprobar(client, crear_caso):
    caso_id = crear_caso(EstadoCaso.DESCARTADO)

    assert _accion(client, caso_id, "pendiente").status_code == 200
    assert _accion(client, caso_id, "aprobar").json()["estado"] == "aprobado"


@pytest.mark.parametrize("accion", ["aprobar", "descartar", "pendiente"])
def test_caso_inexistente(client, accion):
    respuesta = _accion(client, 99, accion)

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detalle": "El caso CP-99 no existe"}


# --- Edición ---------------------------------------------------------------


def test_editar_un_caso_valido_puede_dejarlo_invalido(client, crear_caso):
    caso_id = crear_caso()

    respuesta = client.put(f"/casos/{caso_id}", json={"gherkin": INVALIDO})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["valido"] is False
    assert cuerpo["errores_validacion"] == [ERROR_INVALIDO]
    assert cuerpo["gherkin"] == INVALIDO
    assert client.get("/historias/1").json()["resumen_casos"]["invalidos"] == 1
    assert _accion(client, caso_id, "aprobar").status_code == 409


def test_editar_toma_el_titulo_del_escenario_si_queda_valido(client, crear_caso):
    caso_id = crear_caso()
    nuevo = VALIDO.replace("Escenario: Ingreso exitoso", "Escenario:   Login correcto  ")

    respuesta = client.put(f"/casos/{caso_id}", json={"gherkin": nuevo})

    assert respuesta.json()["titulo"] == "Login correcto"


def test_editar_conserva_el_titulo_si_queda_invalido(client, crear_caso):
    caso_id = crear_caso()
    nuevo = INVALIDO.replace("Escenario: Ingreso exitoso", "Escenario: Otro título")

    respuesta = client.put(f"/casos/{caso_id}", json={"gherkin": nuevo})

    assert respuesta.json()["titulo"] == "Ingreso exitoso"


def test_editar_normaliza_espacios_al_principio_y_al_final(client, crear_caso):
    caso_id = crear_caso()

    respuesta = client.put(f"/casos/{caso_id}", json={"gherkin": f"\n\n{VALIDO}\n\n  "})

    assert respuesta.json()["gherkin"] == VALIDO


@pytest.mark.parametrize("estado", [EstadoCaso.APROBADO, EstadoCaso.DESCARTADO])
def test_solo_se_editan_casos_pendientes(client, crear_caso, estado):
    caso_id = crear_caso(estado)

    respuesta = client.put(f"/casos/{caso_id}", json={"gherkin": INVALIDO})

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detalle": "Solo se pueden editar casos pendientes: volvé CP-1 a pendiente para editarlo."
    }
    assert client.get("/historias/1/casos").json()[0]["gherkin"] == VALIDO


@pytest.mark.parametrize("cuerpo", [{"gherkin": ""}, {"gherkin": "   \n "}, {}])
def test_editar_con_gherkin_vacio_es_422(client, crear_caso, cuerpo):
    caso_id = crear_caso()

    assert client.put(f"/casos/{caso_id}", json=cuerpo).status_code == 422


def test_editar_caso_inexistente(client):
    respuesta = client.put("/casos/99", json={"gherkin": VALIDO})

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detalle": "El caso CP-99 no existe"}
