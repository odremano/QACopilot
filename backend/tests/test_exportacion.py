"""Exportación de los casos aprobados a Playwright (RF-06 / CA-06)."""

import json
import re
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from app.models import CasoPrueba, HistoriaUsuario
from app.models.estados import EstadoCaso, TipoCaso

PROYECTO_PLAYWRIGHT = Path(__file__).resolve().parent.parent / "playwright"

LOGIN = """\
Escenario: Ingreso exitoso
  Dado que estoy en la página de inicio de sesión
  Cuando ingreso el usuario "standard_user"
  Y ingreso la contraseña "secret_sauce"
  Y presiono el botón de ingresar
  Entonces veo el listado de productos
"""
ORDEN = """\
Escenario: Orden por precio
  Dado que inicié sesión como "standard_user"
  Cuando ordeno los productos por "Price (low to high)"
  Entonces veo "Sauce Labs Onesie" como primer producto
"""
CANCELAR = """\
Escenario: Cancelar el checkout
  Dado que inicié sesión como "standard_user"
  Cuando agrego al carrito el producto "Sauce Labs Backpack"
  Y abro el carrito
  Y presiono el botón de checkout
  Y presiono el botón de cancelar
  Entonces veo el título "Your Cart"
"""


@pytest.fixture
def historia(db):
    historia = HistoriaUsuario(titulo="Inicio de sesión", descripcion="Como cliente quiero entrar.")
    db.add(historia)
    db.commit()
    return historia


@pytest.fixture
def agregar_caso(db, historia):
    def agregar(
        gherkin: str, estado: EstadoCaso = EstadoCaso.APROBADO, titulo: str | None = None
    ) -> CasoPrueba:
        caso = CasoPrueba(
            historia_id=historia.id,
            titulo=titulo or gherkin.splitlines()[0].removeprefix("Escenario: "),
            tipo=TipoCaso.POSITIVO,
            gherkin=gherkin,
            estado=estado,
            valido=True,
        )
        db.add(caso)
        db.commit()
        return caso

    return agregar


def _exportar(client, historia_id: int = 1):
    return client.get(f"/historias/{historia_id}/export")


def _titulos_de_tests(contenido: str) -> list[str]:
    return [json.loads(t) for t in re.findall(r'^  test\(("(?:[^"\\]|\\.)*")', contenido, re.M)]


# --- CA-06 -----------------------------------------------------------------


def test_exporta_solo_los_casos_aprobados(client, agregar_caso):
    agregar_caso(LOGIN)
    agregar_caso(ORDEN)
    agregar_caso(LOGIN, EstadoCaso.DESCARTADO)
    agregar_caso(CANCELAR)
    agregar_caso(ORDEN, EstadoCaso.DESCARTADO)
    agregar_caso(LOGIN, EstadoCaso.PENDIENTE)

    respuesta = _exportar(client)

    assert respuesta.status_code == 200
    assert respuesta.headers["content-disposition"] == 'attachment; filename="HU-1.spec.ts"'
    assert respuesta.headers["content-type"].startswith("text/plain")
    assert _titulos_de_tests(respuesta.text) == [
        "[CP-1] Ingreso exitoso",
        "[CP-2] Orden por precio",
        "[CP-4] Cancelar el checkout",
    ]


def test_historia_sin_casos_aprobados(client, agregar_caso):
    agregar_caso(LOGIN, EstadoCaso.PENDIENTE)
    agregar_caso(ORDEN, EstadoCaso.DESCARTADO)

    respuesta = _exportar(client)

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detalle": "HU-1 no tiene casos aprobados: aprobá al menos uno para exportar."
    }


def test_historia_inexistente(client):
    respuesta = _exportar(client, 99)

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detalle": "La historia HU-99 no existe"}


# --- Contenido del archivo ---------------------------------------------------


def test_cada_paso_es_un_test_step_con_el_codigo_de_su_plantilla(client, agregar_caso):
    agregar_caso(ORDEN)

    contenido = _exportar(client).text

    assert contenido == (
        "// Generado por QA Copilot para HU-1 (catálogo saucedemo v2).\n"
        "// Cada paso Gherkin se traduce con la plantilla del catálogo; no editar a mano.\n"
        "import { test, expect } from '@playwright/test';\n"
        "\n"
        'test.describe("[HU-1] Inicio de sesión", () => {\n'
        '  test("[CP-1] Orden por precio", async ({ page }) => {\n'
        '    await test.step("Dado que inicié sesión como \\"standard_user\\"", async () => {\n'
        "      await page.goto('/');\n"
        '      await page.locator(\'[data-test="username"]\').fill("standard_user");\n'
        "      await page.locator('[data-test=\"password\"]').fill('secret_sauce');\n"
        "      await page.locator('[data-test=\"login-button\"]').click();\n"
        "      await expect(page.locator('[data-test=\"inventory-container\"]')).toBeVisible();\n"
        "    });\n"
        '    await test.step("Cuando ordeno los productos por \\"Price (low to high)\\"", '
        "async () => {\n"
        "      await page.locator('[data-test=\"product-sort-container\"]')"
        '.selectOption({ label: "Price (low to high)" });\n'
        "    });\n"
        '    await test.step("Entonces veo \\"Sauce Labs Onesie\\" como primer producto", '
        "async () => {\n"
        "      await expect(page.locator('[data-test=\"inventory-item-name\"]').first())"
        '.toHaveText("Sauce Labs Onesie");\n'
        "    });\n"
        "  });\n"
        "});\n"
    )


def test_el_paso_conserva_la_escritura_del_caso_y_su_valor(client, agregar_caso):
    # La coincidencia ignora mayúsculas y espacios, pero el valor se usa tal cual.
    agregar_caso(LOGIN.replace('el usuario "standard_user"', 'EL   usuario "Standard_User "'))

    contenido = _exportar(client).text

    assert '.fill("Standard_User ");' in contenido
    assert 'test.step("Cuando ingreso EL   usuario \\"Standard_User \\""' in contenido


@pytest.mark.parametrize(
    "valor",
    [
        "'); await page.close(); ('",
        "\\'); process.exit(1); //",
        "${process.exit(1)}",
        "`; process.exit(1); `",
        "</script><script>alert(1)</script>",
        "línea separada",
    ],
)
def test_los_valores_se_escapan_como_literales(client, agregar_caso, valor):
    agregar_caso(LOGIN.replace("standard_user", valor))

    contenido = _exportar(client).text

    literal = json.dumps(valor, ensure_ascii=False).replace("\u2028", "\\u2028")
    assert f"fill({literal});" in contenido
    assert "\u2028" not in contenido
    # El valor solo aparece dentro de literales: en el código del paso y en el nombre del step.
    sin_literales = re.sub(r'"(?:[^"\\]|\\.)*"', '""', contenido)
    assert "process" not in sin_literales
    assert "alert" not in sin_literales
    assert "page.close" not in sin_literales


def test_los_titulos_se_escapan(client, agregar_caso):
    titulo = 'Título con "comillas", \\barras\\ y `backticks` ${x}'
    agregar_caso(LOGIN, titulo=titulo)

    contenido = _exportar(client).text

    assert _titulos_de_tests(contenido) == [f"[CP-1] {titulo}"]


def test_un_caso_aprobado_que_ya_no_coincide_con_el_catalogo_bloquea_la_exportacion(
    client, agregar_caso
):
    # Simula un cambio del catálogo posterior a la aprobación.
    agregar_caso(LOGIN)
    agregar_caso(LOGIN.replace("presiono el botón de ingresar", "hago clic en Login"))

    respuesta = _exportar(client)

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detalle": "CP-2 está aprobado pero ya no es válido con el catálogo actual: Paso 4: "
        "«Y hago clic en Login» no coincide con ningún paso del catálogo. Volvelo a "
        "pendiente y corregilo para poder exportar."
    }


# --- Compilación (CA-06: "el archivo compila sin errores con tsc --noEmit") ----------------


@pytest.mark.slow
def test_el_archivo_exportado_compila_con_tsc(client, agregar_caso):
    agregar_caso(LOGIN)
    agregar_caso(ORDEN)
    agregar_caso(CANCELAR)
    agregar_caso(LOGIN.replace("standard_user", "'); `${x}` \\ //"), titulo='Raro "x"')
    contenido = _exportar(client).text

    # Dentro del proyecto Playwright, para que resuelva '@playwright/test' y use su tsconfig.
    carpeta = PROYECTO_PLAYWRIGHT / f"_tsc_{uuid.uuid4().hex}"
    carpeta.mkdir()
    try:
        (carpeta / "HU-1.spec.ts").write_text(contenido, encoding="utf-8")
        proceso = subprocess.run(
            ["npx", "tsc", "-p", "tsconfig.json"],
            cwd=PROYECTO_PLAYWRIGHT,
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        shutil.rmtree(carpeta)

    assert proceso.returncode == 0, proceso.stdout + proceso.stderr
