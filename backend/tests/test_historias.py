from datetime import datetime

import pytest
from sqlalchemy import func, select

from app.models import CasoPrueba, HistoriaUsuario
from app.seed import HISTORIAS_EJEMPLO, cargar_ejemplos

HISTORIA_VALIDA = {
    "titulo": "Inicio de sesión",
    "descripcion": "Como cliente quiero iniciar sesión para ver los productos.",
    "criterios_aceptacion": "- Ingreso con usuario válido.",
}


def crear(client, **cambios):
    return client.post("/historias", json={**HISTORIA_VALIDA, **cambios})


# --- Alta -----------------------------------------------------------------


def test_crear_historia_valida_devuelve_201_con_codigo(client):
    respuesta = crear(client)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == f"HU-{cuerpo['id']}"
    assert cuerpo["titulo"] == HISTORIA_VALIDA["titulo"]
    assert cuerpo["descripcion"] == HISTORIA_VALIDA["descripcion"]
    assert cuerpo["creada_en"] and cuerpo["actualizada_en"]


def test_crear_recorta_espacios(client):
    cuerpo = crear(client, titulo="  Carrito  ", descripcion="  Como cliente...  ").json()

    assert cuerpo["titulo"] == "Carrito"
    assert cuerpo["descripcion"] == "Como cliente..."


def test_titulo_de_120_caracteres_es_valido(client):
    assert crear(client, titulo="a" * 120).status_code == 201


@pytest.mark.parametrize(
    "titulo",
    ["", "   ", "a" * 121],
    ids=["vacio", "solo-espacios", "121-caracteres"],
)
def test_titulo_invalido_devuelve_422(client, titulo):
    respuesta = crear(client, titulo=titulo)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"][0]["loc"] == ["body", "titulo"]


def test_sin_titulo_devuelve_422(client):
    datos = {k: v for k, v in HISTORIA_VALIDA.items() if k != "titulo"}
    assert client.post("/historias", json=datos).status_code == 422


@pytest.mark.parametrize("descripcion", ["", "   "], ids=["vacia", "solo-espacios"])
def test_descripcion_vacia_devuelve_422(client, descripcion):
    respuesta = crear(client, descripcion=descripcion)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"][0]["loc"] == ["body", "descripcion"]


def test_alta_rechazada_no_guarda(client, db):
    crear(client, titulo="")

    assert db.scalar(select(func.count()).select_from(HistoriaUsuario)) == 0


@pytest.mark.parametrize("criterios", ["", "   \n  ", None], ids=["vacio", "blancos", "nulo"])
def test_criterios_en_blanco_se_guardan_como_null(client, criterios):
    cuerpo = crear(client, criterios_aceptacion=criterios).json()

    assert cuerpo["criterios_aceptacion"] is None


# --- Listado y detalle ----------------------------------------------------


def test_listar_devuelve_resumen_de_casos_en_cero(client):
    crear(client)

    historias = client.get("/historias").json()

    assert len(historias) == 1
    assert historias[0]["codigo"] == "HU-1"
    assert historias[0]["resumen_casos"] == {
        "pendiente": 0,
        "aprobado": 0,
        "descartado": 0,
        "invalidos": 0,
    }


def test_listar_cuenta_casos_por_estado(client, db):
    historia_id = crear(client).json()["id"]
    otra_id = crear(client, titulo="Otra").json()["id"]
    for estado, valido in [("pendiente", True), ("pendiente", False), ("aprobado", True)]:
        db.add(
            CasoPrueba(
                historia_id=historia_id,
                titulo="Caso",
                tipo="positivo",
                gherkin="Escenario: x",
                estado=estado,
                valido=valido,
            )
        )
    db.commit()

    resumenes = {h["id"]: h["resumen_casos"] for h in client.get("/historias").json()}

    assert resumenes[historia_id] == {
        "pendiente": 2,
        "aprobado": 1,
        "descartado": 0,
        "invalidos": 1,
    }
    assert resumenes[otra_id]["pendiente"] == 0


def test_listar_ordena_por_actualizacion_descendente(client):
    primera = crear(client, titulo="Primera").json()["id"]
    segunda = crear(client, titulo="Segunda").json()["id"]
    client.put(f"/historias/{primera}", json={**HISTORIA_VALIDA, "titulo": "Primera editada"})

    ids = [h["id"] for h in client.get("/historias").json()]

    assert ids == [primera, segunda]


def test_obtener_historia(client):
    historia_id = crear(client).json()["id"]

    respuesta = client.get(f"/historias/{historia_id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["criterios_aceptacion"] == HISTORIA_VALIDA["criterios_aceptacion"]


def test_obtener_inexistente_devuelve_404_con_detalle(client):
    respuesta = client.get("/historias/999")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detalle": "La historia HU-999 no existe"}


# --- Edición --------------------------------------------------------------


def test_editar_actualiza_campos_y_fecha(client):
    original = crear(client).json()

    respuesta = client.put(
        f"/historias/{original['id']}",
        json={"titulo": "Nuevo título", "descripcion": "Nueva descripción"},
    )

    assert respuesta.status_code == 200
    editada = respuesta.json()
    assert editada["titulo"] == "Nuevo título"
    assert editada["descripcion"] == "Nueva descripción"
    assert editada["criterios_aceptacion"] is None
    assert editada["creada_en"] == original["creada_en"]
    assert datetime.fromisoformat(editada["actualizada_en"]) > datetime.fromisoformat(
        original["actualizada_en"]
    )
    assert client.get(f"/historias/{original['id']}").json()["titulo"] == "Nuevo título"


def test_editar_con_titulo_vacio_devuelve_422(client):
    historia_id = crear(client).json()["id"]

    respuesta = client.put(f"/historias/{historia_id}", json={**HISTORIA_VALIDA, "titulo": " "})

    assert respuesta.status_code == 422
    assert client.get(f"/historias/{historia_id}").json()["titulo"] == HISTORIA_VALIDA["titulo"]


def test_editar_inexistente_devuelve_404(client):
    respuesta = client.put("/historias/999", json=HISTORIA_VALIDA)

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detalle": "La historia HU-999 no existe"}


# --- Salud y seed ---------------------------------------------------------


def test_salud_ok(client):
    respuesta = client.get("/salud")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["base_de_datos"] == "ok"
    assert cuerpo["version"] == "0.1.0"
    assert set(cuerpo["llm"]) == {"proveedor", "modelo", "configurado"}


def test_seed_es_idempotente(db):
    assert cargar_ejemplos(db) == len(HISTORIAS_EJEMPLO) == 3
    assert cargar_ejemplos(db) == 0

    titulos = db.scalars(select(HistoriaUsuario.titulo).order_by(HistoriaUsuario.id)).all()
    assert titulos == ["Inicio de sesión", "Carrito de compras", "Checkout"]
