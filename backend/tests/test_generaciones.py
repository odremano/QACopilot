"""Generación de casos (RF-03 / CA-03), reintentos (CA-04), regeneración (CA-11), límite diario
(RNF-08) y modo demo (CA-10). Ninguna prueba llama a la red: el proveedor es un doble."""

import json

import pytest
from sqlalchemy import select

from app.config import settings
from app.main import app
from app.models import CasoPrueba, Generacion
from app.models.estados import EstadoCaso
from app.seed import HISTORIAS_EJEMPLO
from app.services.llm import ErrorProveedor, obtener_proveedor

HISTORIA = {
    "titulo": "Inicio de sesión",
    "descripcion": "Como cliente quiero iniciar sesión para comprar.",
    "criterios_aceptacion": "- Con un usuario válido veo los productos.",
}

INGRESO = [
    "Dado que estoy en la página de inicio de sesión",
    'Cuando ingreso el usuario "standard_user"',
    'Y ingreso la contraseña "secret_sauce"',
    "Y presiono el botón de ingresar",
    "Entonces veo el listado de productos",
]
BLOQUEADO = [
    "Dado que estoy en la página de inicio de sesión",
    'Cuando ingreso el usuario "locked_out_user"',
    'Y ingreso la contraseña "secret_sauce"',
    "Y presiono el botón de ingresar",
    'Entonces veo el mensaje de error "Epic sadface: Sorry, this user has been locked out."',
]
FUERA_DEL_CATALOGO = ["Dado que estoy en la página de inicio de sesión", "Cuando hago magia"]


def _respuesta(*casos: tuple[str, str, list[str]]) -> str:
    return json.dumps(
        {"casos": [{"titulo": t, "tipo": tipo, "pasos": p} for t, tipo, p in casos]},
        ensure_ascii=False,
    )


VALIDA = _respuesta(
    ("Ingreso exitoso", "positivo", INGRESO),
    ("Usuario bloqueado", "negativo", BLOQUEADO),
    ("Paso inventado", "limite", FUERA_DEL_CATALOGO),
)


class ProveedorFalso:
    """Devuelve las respuestas en orden; una excepción en la lista se lanza."""

    nombre = "falso"
    modelo = "modelo-falso"

    def __init__(self, *respuestas: str | Exception) -> None:
        self.respuestas = list(respuestas)
        self.llamadas = 0
        self.mensajes: list[dict] = []

    def completar(self, mensajes, historia) -> str:
        self.llamadas += 1
        self.mensajes = mensajes
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


@pytest.fixture
def usar_proveedor(client):
    def configurar(*respuestas: str | Exception) -> ProveedorFalso:
        proveedor = ProveedorFalso(*respuestas)
        app.dependency_overrides[obtener_proveedor] = lambda: proveedor
        return proveedor

    return configurar


@pytest.fixture
def historia_id(client) -> int:
    return client.post("/historias", json=HISTORIA).json()["id"]


def _generar(client, historia_id: int):
    return client.post(f"/historias/{historia_id}/generaciones")


def _generaciones(db) -> list[Generacion]:
    return list(db.scalars(select(Generacion).order_by(Generacion.id)))


# --- Generación (CA-03 / CA-04) --------------------------------------------


def test_generacion_crea_casos_pendientes_y_marca_los_invalidos(
    client, usar_proveedor, historia_id
):
    proveedor = usar_proveedor(VALIDA)

    respuesta = _generar(client, historia_id)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert (cuerpo["proveedor"], cuerpo["modelo"], cuerpo["version_prompt"]) == (
        "falso",
        "modelo-falso",
        "v1",
    )
    assert (cuerpo["casos_validos"], cuerpo["casos_invalidos"]) == (2, 1)
    casos = cuerpo["casos"]
    assert [c["codigo"] for c in casos] == ["CP-1", "CP-2", "CP-3"]
    assert {c["estado"] for c in casos} == {"pendiente"}
    assert casos[0]["gherkin"].startswith("Escenario: Ingreso exitoso\n  Dado que estoy")
    assert casos[0]["errores_validacion"] == []
    assert casos[2]["valido"] is False
    assert casos[2]["errores_validacion"] == [
        "Paso 2: «Cuando hago magia» no coincide con ningún paso del catálogo."
    ]
    assert proveedor.llamadas == 1


def test_el_prompt_incluye_la_historia_y_el_catalogo(client, usar_proveedor, historia_id):
    proveedor = usar_proveedor(VALIDA)

    _generar(client, historia_id)

    sistema, usuario = (m["content"] for m in proveedor.mensajes)
    assert 'ingreso el usuario "{texto}"' in sistema
    assert "Epic sadface: Username is required" in sistema
    assert '"pasos"' in sistema
    assert "json" in sistema
    assert HISTORIA["descripcion"] in usuario
    assert HISTORIA["criterios_aceptacion"] in usuario


def test_listar_casos_de_la_historia(client, usar_proveedor, historia_id):
    usar_proveedor(VALIDA)
    _generar(client, historia_id)

    respuesta = client.get(f"/historias/{historia_id}/casos")

    assert respuesta.status_code == 200
    assert [c["titulo"] for c in respuesta.json()] == [
        "Ingreso exitoso",
        "Usuario bloqueado",
        "Paso inventado",
    ]
    resumen = client.get(f"/historias/{historia_id}").json()["resumen_casos"]
    assert resumen == {"pendiente": 3, "aprobado": 0, "descartado": 0, "invalidos": 1}


def test_respuesta_con_formato_invalido_se_reintenta(client, usar_proveedor, historia_id, db):
    proveedor = usar_proveedor("", "Acá van los casos", VALIDA)

    respuesta = _generar(client, historia_id)

    assert respuesta.status_code == 201
    assert proveedor.llamadas == 3
    intentos = _generaciones(db)[0].respuesta_cruda["intentos"]
    assert [i["error"] for i in intentos] == [
        "El modelo devolvió una respuesta vacía.",
        "La respuesta del modelo no es JSON válido.",
        None,
    ]


def test_si_el_formato_sigue_invalido_se_informa_y_se_registra(
    client, usar_proveedor, historia_id, db
):
    usar_proveedor("{}", "{}", "{}")

    respuesta = _generar(client, historia_id)

    assert respuesta.status_code == 502
    assert respuesta.json() == {
        "detalle": "La respuesta del modelo no respeta el formato esperado. Se intentó 3 veces."
    }
    (generacion,) = _generaciones(db)
    assert generacion.estado == "error"
    assert generacion.mensaje_error == respuesta.json()["detalle"]
    assert len(generacion.respuesta_cruda["intentos"]) == 3
    assert client.get(f"/historias/{historia_id}").status_code == 200
    assert client.get(f"/historias/{historia_id}/casos").json() == []


@pytest.mark.parametrize(
    ("respuesta", "mensaje"),
    [
        (
            _respuesta(("a", "positivo", INGRESO), ("b", "positivo", INGRESO)),
            "El modelo propuso 2 casos y deben ser entre 3 y 8.",
        ),
        (
            _respuesta(*[("a", "negativo", BLOQUEADO)] * 9),
            "El modelo propuso 9 casos y deben ser entre 3 y 8.",
        ),
        (
            _respuesta(*[("a", "positivo", INGRESO)] * 3),
            "El modelo no propuso al menos un caso positivo y uno negativo.",
        ),
    ],
)
def test_reglas_de_la_generacion_se_reintentan(
    client, usar_proveedor, historia_id, respuesta, mensaje
):
    proveedor = usar_proveedor(respuesta, respuesta, respuesta)

    resultado = _generar(client, historia_id)

    assert resultado.status_code == 502
    assert resultado.json()["detalle"].startswith(mensaje)
    assert proveedor.llamadas == 3


def test_falla_del_proveedor_no_se_reintenta(client, usar_proveedor, historia_id, db):
    proveedor = usar_proveedor(ErrorProveedor("El proveedor del LLM no respondió a tiempo."))

    respuesta = _generar(client, historia_id)

    assert respuesta.status_code == 502
    assert respuesta.json() == {"detalle": "El proveedor del LLM no respondió a tiempo."}
    assert proveedor.llamadas == 1
    assert _generaciones(db)[0].estado == "error"


def test_historia_inexistente(client, usar_proveedor):
    usar_proveedor(VALIDA)

    respuesta = _generar(client, 999)

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detalle": "La historia HU-999 no existe"}
    assert client.get("/historias/999/casos").status_code == 404


# --- Regeneración (CA-11) --------------------------------------------------


def test_regenerar_conserva_aprobados_y_descartados_y_reemplaza_pendientes(
    client, usar_proveedor, historia_id, db
):
    usar_proveedor(VALIDA, VALIDA)
    _generar(client, historia_id)
    db.get(CasoPrueba, 1).estado = EstadoCaso.APROBADO
    db.get(CasoPrueba, 2).estado = EstadoCaso.DESCARTADO
    db.commit()

    respuesta = _generar(client, historia_id)

    assert respuesta.status_code == 201
    casos = client.get(f"/historias/{historia_id}/casos").json()
    assert [(c["id"], c["estado"]) for c in casos] == [
        (1, "aprobado"),
        (2, "descartado"),
        (4, "pendiente"),
        (5, "pendiente"),
        (6, "pendiente"),
    ]


def test_si_la_regeneracion_falla_los_casos_anteriores_se_conservan(
    client, usar_proveedor, historia_id
):
    usar_proveedor(VALIDA, ErrorProveedor("Falla"))
    _generar(client, historia_id)

    assert _generar(client, historia_id).status_code == 502
    assert len(client.get(f"/historias/{historia_id}/casos").json()) == 3


# --- Límite diario (RNF-08) ------------------------------------------------


def test_limite_diario(client, usar_proveedor, historia_id, monkeypatch):
    monkeypatch.setattr(settings, "daily_generation_limit", 2)
    proveedor = usar_proveedor(VALIDA, ErrorProveedor("Falla"), VALIDA)
    assert _generar(client, historia_id).status_code == 201
    assert _generar(client, historia_id).status_code == 502  # las fallidas también cuentan

    respuesta = _generar(client, historia_id)

    assert respuesta.status_code == 429
    assert respuesta.json() == {
        "detalle": "Se alcanzó el límite diario de 2 generaciones. Probá de nuevo mañana."
    }
    assert proveedor.llamadas == 2


def test_limite_cero_desactiva_el_control(client, usar_proveedor, historia_id, monkeypatch):
    monkeypatch.setattr(settings, "daily_generation_limit", 0)
    usar_proveedor(VALIDA, VALIDA)

    assert _generar(client, historia_id).status_code == 201
    assert _generar(client, historia_id).status_code == 201


# --- Configuración y modo demo (CA-10) -------------------------------------


def test_sin_clave_la_generacion_no_esta_disponible(client, historia_id, monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openrouter")
    monkeypatch.setattr(settings, "llm_api_key", None)

    respuesta = _generar(client, historia_id)

    assert respuesta.status_code == 503
    assert "falta configurar LLM_API_KEY" in respuesta.json()["detalle"]


def test_proveedor_desconocido(client, historia_id, monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "chatgpt")

    respuesta = _generar(client, historia_id)

    assert respuesta.status_code == 503
    assert "LLM_PROVIDER='chatgpt' no es válido" in respuesta.json()["detalle"]


def test_modo_demo_con_historia_sin_respuesta_pregrabada(client, historia_id, monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "demo")
    client.put(f"/historias/{historia_id}", json=HISTORIA | {"titulo": "Otra historia"})

    respuesta = _generar(client, historia_id)

    assert respuesta.status_code == 502
    assert "solo tiene respuestas para las historias de ejemplo" in respuesta.json()["detalle"]


@pytest.mark.parametrize("ejemplo", HISTORIAS_EJEMPLO, ids=lambda h: h["titulo"])
def test_modo_demo_genera_casos_validos_para_cada_historia_de_ejemplo(client, monkeypatch, ejemplo):
    monkeypatch.setattr(settings, "llm_provider", "demo")
    monkeypatch.setattr(settings, "llm_api_key", None)  # no hace falta clave
    historia_id = client.post("/historias", json=ejemplo).json()["id"]

    respuesta = _generar(client, historia_id)

    assert respuesta.status_code == 201, respuesta.json()
    cuerpo = respuesta.json()
    assert (cuerpo["proveedor"], cuerpo["modelo"]) == ("demo", "respuestas-pregrabadas")
    assert cuerpo["casos_invalidos"] == 0
