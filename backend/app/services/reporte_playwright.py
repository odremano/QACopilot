"""Lectura del reporte JSON de Playwright (RF-08, spec 9.4).

Cada test se asocia a su caso por el código [CP-n] del título. El mensaje de error se limpia
(sin colores ANSI ni el «Call log» interno) y se le antepone el paso Gherkin que falló, que
el exportador declara con test.step.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models.estados import EstadoResultado

LIMITE_MENSAJE = 4000
_CODIGO_CASO = re.compile(r"^\[CP-(\d+)\]")
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_ESTADOS = {
    "expected": EstadoResultado.APROBADO,
    "flaky": EstadoResultado.APROBADO,
    "unexpected": EstadoResultado.FALLIDO,
    "skipped": EstadoResultado.OMITIDO,
}


@dataclass(frozen=True)
class ResultadoTest:
    caso_id: int
    estado: EstadoResultado
    duracion_ms: int
    mensaje_error: str | None
    captura: Path | None


def leer_reporte(reporte: dict[str, Any]) -> list[ResultadoTest]:
    """Resultados de los tests cuyo título empieza con [CP-n], en el orden del reporte."""
    return [_resultado(spec) for spec in _specs(reporte.get("suites", [])) if _caso_id(spec)]


def errores_globales(reporte: dict[str, Any]) -> list[str]:
    """Errores que impidieron correr los tests (por ejemplo, un archivo que no compila)."""
    return [limpiar(error.get("message", "")) for error in reporte.get("errors", [])]


def limpiar(texto: str) -> str:
    return _ANSI.sub("", texto).strip()


def _specs(suites: list[dict]) -> list[dict]:
    specs: list[dict] = []
    for suite in suites:
        specs += suite.get("specs", [])
        specs += _specs(suite.get("suites", []))
    return specs


def _caso_id(spec: dict) -> int | None:
    encontrado = _CODIGO_CASO.match(spec.get("title", ""))
    return int(encontrado.group(1)) if encontrado else None


def _resultado(spec: dict) -> ResultadoTest:
    # Un solo proyecto (Chromium) y sin reintentos: un test con un resultado por spec.
    test = spec["tests"][0]
    resultados = test.get("results", [])
    ultimo = resultados[-1] if resultados else {}
    estado = _ESTADOS.get(test.get("status"), EstadoResultado.FALLIDO)
    return ResultadoTest(
        caso_id=_caso_id(spec),
        estado=estado,
        duracion_ms=round(sum(r.get("duration", 0) for r in resultados)),
        mensaje_error=_mensaje_error(ultimo) if estado == EstadoResultado.FALLIDO else None,
        captura=_captura(ultimo),
    )


def _mensaje_error(resultado: dict) -> str:
    error = resultado.get("error") or next(iter(resultado.get("errors", [])), None) or {}
    mensaje = limpiar(error.get("message", "")) or "El test falló sin mensaje de error."
    mensaje = mensaje.split("\n\nCall log:")[0].removeprefix("Error: ").strip()
    if paso := next((p["title"] for p in resultado.get("steps", []) if p.get("error")), None):
        mensaje = f"Falló el paso «{paso}».\n\n{mensaje}"
    return mensaje[:LIMITE_MENSAJE]


def _captura(resultado: dict) -> Path | None:
    for adjunto in resultado.get("attachments", []):
        if adjunto.get("contentType") == "image/png" and adjunto.get("path"):
            return Path(adjunto["path"])
    return None
