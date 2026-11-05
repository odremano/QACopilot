"""Ejecución con Playwright y resultados (RF-07 / CA-07, RF-08 / CA-08).

Salvo la prueba lenta del final, Playwright se reemplaza por un runner falso que devuelve el
reporte real de muestra. El TestClient corre las tareas en segundo plano apenas termina la
respuesta, así que después del POST la ejecución ya terminó.
"""

from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.db import get_fabrica_sesiones
from app.main import app
from app.models import CasoPrueba, Ejecucion, HistoriaUsuario, ResultadoCaso
from app.models.estados import EstadoCaso, EstadoEjecucion, EstadoResultado, TipoCaso
from app.services.ejecuciones import marcar_interrumpidas
from app.services.runner import RunnerPlaywright, SalidaRunner, TiempoAgotado, obtener_runner
from tests.test_reporte_playwright import reporte_de_muestra

BLOQUEADO = """\
Escenario: Usuario bloqueado
  Dado que estoy en la página de inicio de sesión
  Cuando ingreso el usuario "locked_out_user"
  Y ingreso la contraseña "secret_sauce"
  Y presiono el botón de ingresar
  Entonces veo el mensaje de error "Epic sadface: Sorry, this user has been locked out."
"""
TOTAL_INCORRECTO = """\
Escenario: Total incorrecto
  Dado que inicié sesión como "standard_user"
  Cuando agrego al carrito el producto "Sauce Labs Backpack"
  Y abro el carrito
  Y presiono el botón de checkout
  Y ingreso el nombre "Ana"
  Y ingreso el apellido "Pérez"
  Y ingreso el código postal "1425"
  Y presiono el botón de continuar
  Entonces veo el total "Total: $99.99"
"""
PNG = b"\x89PNG\r\n\x1a\n captura"


class RunnerFalso:
    """Devuelve el reporte de muestra con [CP-7] y [CP-8] cambiados por los casos 1 y 2."""

    def __init__(self, reporte="muestra", error: Exception | None = None) -> None:
        self.reporte = reporte
        self.error = error
        self.llamadas: list[tuple[str, str, Path]] = []

    def ejecutar(self, nombre: str, contenido: str, salida: Path) -> SalidaRunner:
        self.llamadas.append((nombre, contenido, salida))
        if self.error:
            raise self.error
        reporte = self.reporte
        if reporte == "muestra":
            reporte = reporte_de_muestra(salida, {7: 1, 8: 2})
            ruta = Path(reporte["suites"][0]["suites"][0]["specs"][1]["tests"][0]["results"][0]
                        ["attachments"][0]["path"])  # fmt: skip
            ruta.parent.mkdir(parents=True)
            ruta.write_bytes(PNG)
        return SalidaRunner(codigo_salida=1, log="  2 tests\n  1 failed", reporte=reporte)


@pytest.fixture
def runner(monkeypatch, tmp_path, session_factory, client):
    monkeypatch.setattr(settings, "evidencias_dir", str(tmp_path))
    falso = RunnerFalso()
    app.dependency_overrides[obtener_runner] = lambda: falso
    app.dependency_overrides[get_fabrica_sesiones] = lambda: session_factory
    return falso


@pytest.fixture
def historia(db):
    historia = HistoriaUsuario(titulo="Inicio de sesión", descripcion="Como cliente quiero entrar.")
    db.add(historia)
    db.commit()
    return historia


@pytest.fixture
def aprobar(db, historia):
    def aprobar(gherkin: str, estado: EstadoCaso = EstadoCaso.APROBADO) -> CasoPrueba:
        caso = CasoPrueba(
            historia_id=historia.id,
            titulo=gherkin.splitlines()[0].removeprefix("Escenario: "),
            tipo=TipoCaso.POSITIVO,
            gherkin=gherkin,
            estado=estado,
            valido=True,
        )
        db.add(caso)
        db.commit()
        return caso

    return aprobar


def _iniciar(client, historia_id: int = 1):
    return client.post(f"/historias/{historia_id}/ejecuciones")


# --- CA-07 -----------------------------------------------------------------


def test_la_ejecucion_arranca_en_curso_y_termina_finalizada(client, runner, aprobar):
    aprobar(BLOQUEADO)
    aprobar(TOTAL_INCORRECTO)

    respuesta = _iniciar(client)

    assert respuesta.status_code == 202
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "en_curso"
    assert cuerpo["total"] == 2
    assert cuerpo["porcentaje_exito"] is None
    assert cuerpo["historia"] == {"id": 1, "codigo": "HU-1", "titulo": "Inicio de sesión"}

    detalle = client.get(f"/ejecuciones/{cuerpo['id']}").json()
    assert detalle["estado"] == "finalizada"
    assert detalle["finalizada_en"] is not None
    assert (detalle["total"], detalle["aprobados"], detalle["fallidos"]) == (2, 1, 1)
    assert detalle["omitidos"] == 0
    assert detalle["porcentaje_exito"] == 50.0
    assert detalle["log"] == "2 tests\n  1 failed"


def test_se_ejecuta_el_mismo_spec_que_se_exporta(client, runner, aprobar, tmp_path):
    aprobar(BLOQUEADO)

    _iniciar(client)

    ((nombre, contenido, salida),) = runner.llamadas
    assert nombre == "HU-1.spec.ts"
    assert contenido == client.get("/historias/1/export").text
    assert salida == tmp_path / "ejecuciones" / "1"


def test_no_se_puede_iniciar_otra_ejecucion_en_curso(client, runner, db, historia, aprobar):
    aprobar(BLOQUEADO)
    db.add(Ejecucion(historia_id=historia.id, estado=EstadoEjecucion.EN_CURSO))
    db.commit()

    respuesta = _iniciar(client)

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detalle": "Ya hay una ejecución en curso (ejecución 1 de HU-1). Esperá a que "
        "termine para iniciar otra."
    }
    assert runner.llamadas == []


def test_la_base_impide_dos_ejecuciones_en_curso(db, historia):
    db.add(Ejecucion(historia_id=historia.id, estado=EstadoEjecucion.EN_CURSO))
    db.commit()
    db.add(Ejecucion(historia_id=historia.id, estado=EstadoEjecucion.EN_CURSO))

    with pytest.raises(IntegrityError, match="ux_ejecucion_una_en_curso"):
        db.commit()


def test_terminada_una_se_puede_iniciar_otra(client, runner, aprobar):
    aprobar(BLOQUEADO)

    assert _iniciar(client).status_code == 202
    assert _iniciar(client).status_code == 202
    assert [e["id"] for e in client.get("/ejecuciones").json()] == [2, 1]


def test_sin_casos_aprobados_no_se_ejecuta(client, runner, aprobar):
    aprobar(BLOQUEADO, EstadoCaso.PENDIENTE)

    respuesta = _iniciar(client)

    assert respuesta.status_code == 409
    assert respuesta.json()["detalle"].startswith("HU-1 no tiene casos aprobados")
    assert client.get("/ejecuciones").json() == []


def test_historia_inexistente(client, runner):
    assert _iniciar(client, 99).status_code == 404


# --- CA-08 -----------------------------------------------------------------


def test_caso_fallido_con_su_error_y_su_captura(client, runner, aprobar):
    aprobar(BLOQUEADO)
    aprobar(TOTAL_INCORRECTO)
    _iniciar(client)

    aprobado, fallido = client.get("/ejecuciones/1").json()["resultados"]

    assert aprobado["caso"] == {"id": 1, "codigo": "CP-1", "titulo": "Usuario bloqueado"}
    assert aprobado["estado"] == "aprobado"
    assert aprobado["mensaje_error"] is None
    assert aprobado["url_captura"] is None
    assert fallido["estado"] == "fallido"
    assert fallido["mensaje_error"].startswith(
        'Falló el paso «Entonces veo el total "Total: $99.99"».'
    )
    assert fallido["url_captura"] == f"/evidencias/{fallido['id']}"
    assert "ruta_captura" not in fallido

    captura = client.get(fallido["url_captura"])
    assert captura.status_code == 200
    assert captura.headers["content-type"] == "image/png"
    assert captura.content == PNG


def test_un_caso_que_no_aparece_en_el_reporte_queda_omitido(client, runner, aprobar):
    aprobar(BLOQUEADO)
    aprobar(TOTAL_INCORRECTO)
    aprobar(BLOQUEADO)  # CP-3: el reporte de muestra solo trae CP-1 y CP-2

    _iniciar(client)

    detalle = client.get("/ejecuciones/1").json()
    assert (detalle["aprobados"], detalle["fallidos"], detalle["omitidos"]) == (1, 1, 1)
    assert detalle["resultados"][2]["estado"] == "omitido"
    assert detalle["resultados"][2]["mensaje_error"] == (
        "No se ejecutó: el test no aparece en el reporte de Playwright."
    )


@pytest.mark.parametrize(
    ("falla", "log"),
    [
        (
            RunnerFalso(error=TiempoAgotado("La ejecución superó el tiempo máximo.")),
            "La ejecución superó el tiempo máximo.",
        ),
        (
            RunnerFalso(error=FileNotFoundError("playwright")),
            "No se pudo correr Playwright: playwright",
        ),
        (RunnerFalso(reporte=None), "Playwright no generó el reporte.\n\n2 tests\n  1 failed"),
        (
            RunnerFalso(reporte={"suites": [], "errors": [{"message": "SyntaxError: x"}]}),
            "SyntaxError: x\n\n2 tests\n  1 failed",
        ),
    ],
)
def test_si_playwright_falla_la_ejecucion_queda_con_error(client, runner, aprobar, falla, log):
    app.dependency_overrides[obtener_runner] = lambda: falla
    aprobar(BLOQUEADO)

    _iniciar(client)

    detalle = client.get("/ejecuciones/1").json()
    assert detalle["estado"] == "error"
    assert detalle["finalizada_en"] is not None
    assert detalle["log"] == log
    assert detalle["resultados"] == []
    assert detalle["porcentaje_exito"] is None
    assert _iniciar(client).status_code == 202  # no quedó bloqueada


# --- Consultas y evidencias ---------------------------------------------------------------


def test_listar_filtra_por_historia(client, runner, db, aprobar):
    aprobar(BLOQUEADO)
    otra = HistoriaUsuario(titulo="Carrito", descripcion="Como cliente quiero comprar.")
    db.add(otra)
    db.commit()
    db.add(Ejecucion(historia_id=otra.id, estado=EstadoEjecucion.FINALIZADA))
    db.commit()
    _iniciar(client)

    assert [e["id"] for e in client.get("/ejecuciones").json()] == [2, 1]
    assert [e["id"] for e in client.get("/ejecuciones?historia_id=1").json()] == [2]


def test_ejecucion_inexistente(client):
    respuesta = client.get("/ejecuciones/99")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detalle": "La ejecución 99 no existe"}


@pytest.mark.parametrize("ruta", [None, "no/existe.png", "../../../etc/passwd"])
def test_evidencia_inexistente_o_fuera_de_la_carpeta(client, runner, db, aprobar, ruta):
    caso = aprobar(BLOQUEADO)
    ejecucion = Ejecucion(historia_id=caso.historia_id, estado=EstadoEjecucion.FINALIZADA)
    db.add(ejecucion)
    db.commit()
    resultado = ResultadoCaso(
        ejecucion_id=ejecucion.id,
        caso_id=caso.id,
        estado=EstadoResultado.FALLIDO,
        ruta_captura=ruta,
    )
    db.add(resultado)
    db.commit()

    respuesta = client.get(f"/evidencias/{resultado.id}")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detalle": f"No hay captura para el resultado {resultado.id}"}


def test_al_arrancar_se_marcan_las_ejecuciones_interrumpidas(db, historia):
    db.add(Ejecucion(historia_id=historia.id, estado=EstadoEjecucion.FINALIZADA))
    db.add(Ejecucion(historia_id=historia.id, estado=EstadoEjecucion.EN_CURSO))
    db.commit()

    assert marcar_interrumpidas(db) == 1

    finalizada, interrumpida = db.query(Ejecucion).order_by(Ejecucion.id).all()
    assert finalizada.estado == EstadoEjecucion.FINALIZADA
    assert interrumpida.estado == EstadoEjecucion.ERROR
    assert interrumpida.log == "El backend se reinició mientras la ejecución estaba en curso."


# --- De punta a punta (Playwright real contra SauceDemo) -------------------------------------


@pytest.mark.slow
def test_ejecucion_real_contra_saucedemo(client, runner, aprobar, tmp_path):
    app.dependency_overrides[obtener_runner] = lambda: RunnerPlaywright(tiempo_maximo_s=180)
    aprobar(BLOQUEADO)
    aprobar(TOTAL_INCORRECTO)

    _iniciar(client)

    detalle = client.get("/ejecuciones/1").json()
    assert detalle["estado"] == "finalizada", detalle["log"]
    assert (detalle["aprobados"], detalle["fallidos"]) == (1, 1)
    fallido = detalle["resultados"][1]
    assert 'Received string:    "Total: $32.39"' in fallido["mensaje_error"]
    captura = client.get(fallido["url_captura"])
    assert captura.content.startswith(b"\x89PNG")
    assert (tmp_path / "ejecuciones" / "1" / "HU-1.spec.ts").is_file()
    carpeta_trabajo = Path(RunnerPlaywright().proyecto) / "ejecuciones" / "1"
    assert not carpeta_trabajo.exists()
