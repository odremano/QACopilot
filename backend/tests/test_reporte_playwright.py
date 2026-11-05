"""Lectura del reporte JSON de Playwright (RF-08) con un reporte real como muestra.

datos/reporte_playwright.json salió de correr un .spec.ts exportado contra SauceDemo con un
caso que pasa ([CP-7]) y otro que falla a propósito ([CP-8], total incorrecto). Las rutas
de las capturas tienen {SALIDA} en lugar de la carpeta original.
"""

import json
from pathlib import Path

from app.models.estados import EstadoResultado
from app.services.reporte_playwright import errores_globales, leer_reporte

MUESTRA = Path(__file__).parent / "datos" / "reporte_playwright.json"


def reporte_de_muestra(salida: Path | str = "/salida", codigos: dict[int, int] | None = None):
    texto = MUESTRA.read_text(encoding="utf-8").replace("{SALIDA}", str(salida))
    for original, nuevo in (codigos or {}).items():
        texto = texto.replace(f"[CP-{original}]", f"[CP-{nuevo}]")
    return json.loads(texto)


def test_lee_un_resultado_por_caso():
    aprobado, fallido = leer_reporte(reporte_de_muestra())

    assert (aprobado.caso_id, aprobado.estado) == (7, EstadoResultado.APROBADO)
    assert aprobado.mensaje_error is None
    assert aprobado.captura is None
    assert aprobado.duracion_ms == 758
    assert (fallido.caso_id, fallido.estado) == (8, EstadoResultado.FALLIDO)
    assert fallido.duracion_ms == 5911


def test_el_error_nombra_el_paso_que_fallo_y_queda_legible():
    _, fallido = leer_reporte(reporte_de_muestra())

    assert fallido.mensaje_error.startswith(
        'Falló el paso «Entonces veo el total "Total: $99.99"».\n\n'
        "expect(locator).toContainText(expected) failed"
    )
    assert 'Expected substring: "Total: $99.99"' in fallido.mensaje_error
    assert 'Received string:    "Total: $32.39"' in fallido.mensaje_error
    assert "\x1b" not in fallido.mensaje_error
    assert "Call log" not in fallido.mensaje_error


def test_la_captura_es_el_png_del_fallo():
    _, fallido = leer_reporte(reporte_de_muestra("/evidencias/ejecuciones/3"))

    assert fallido.captura == Path(
        "/evidencias/ejecuciones/3/artefactos/"
        "_prueba-HU-9--HU-9-Prueba-CP-8-Total-incorrecto-chromium/test-failed-1.png"
    )


def test_ignora_los_tests_sin_codigo_de_caso():
    reporte = reporte_de_muestra()
    reporte["suites"][0]["suites"][0]["specs"][0]["title"] = "Un test cualquiera"

    assert [r.caso_id for r in leer_reporte(reporte)] == [8]


def test_un_test_omitido():
    reporte = reporte_de_muestra()
    reporte["suites"][0]["suites"][0]["specs"][0]["tests"][0]["status"] = "skipped"

    assert leer_reporte(reporte)[0].estado == EstadoResultado.OMITIDO


def test_errores_globales_sin_colores():
    reporte = {"suites": [], "errors": [{"message": "\x1b[31mSyntaxError\x1b[39m: algo"}]}

    assert errores_globales(reporte) == ["SyntaxError: algo"]
    assert leer_reporte(reporte) == []
