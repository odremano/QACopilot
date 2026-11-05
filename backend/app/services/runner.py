"""Runner de Playwright (RF-07, spec 9.4): corre un .spec.ts y devuelve su reporte JSON.

El archivo se escribe dentro del proyecto Playwright del backend (para que resuelva
'@playwright/test' y use su playwright.config.ts) y las salidas van a la carpeta de
evidencias. Chromium headless, un worker, sin reintentos y 30 s por test (RNF-09).
"""

import json
import logging
import os
import shutil
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Protocol

from fastapi import Depends

from app.config import settings

logger = logging.getLogger(__name__)

PROYECTO_PLAYWRIGHT = Path(__file__).resolve().parents[2] / "playwright"
TIEMPO_MAXIMO_S = 600
LIMITE_LOG = 20_000


class TiempoAgotado(Exception):
    """La ejecución superó el tiempo máximo y se cortó."""


@dataclass(frozen=True)
class SalidaRunner:
    codigo_salida: int
    log: str
    reporte: dict[str, Any] | None
    """Reporte JSON de Playwright, o None si no se generó (por ejemplo, si no arrancó)."""


class Runner(Protocol):
    def ejecutar(self, nombre: str, contenido: str, salida: Path) -> SalidaRunner: ...


class RunnerPlaywright:
    def __init__(
        self, proyecto: Path = PROYECTO_PLAYWRIGHT, tiempo_maximo_s: int = TIEMPO_MAXIMO_S
    ) -> None:
        self.proyecto = proyecto
        self.tiempo_maximo_s = tiempo_maximo_s

    def ejecutar(self, nombre: str, contenido: str, salida: Path) -> SalidaRunner:
        salida.mkdir(parents=True, exist_ok=True)
        (salida / nombre).write_text(contenido, encoding="utf-8")  # queda como evidencia
        trabajo = self.proyecto / "ejecuciones" / salida.name
        trabajo.mkdir(parents=True, exist_ok=True)
        (trabajo / nombre).write_text(contenido, encoding="utf-8")
        entorno = {
            **os.environ,
            "PW_SALIDA_DIR": str(salida),
            "SUT_BASE_URL": settings.sut_base_url,
            "FORCE_COLOR": "0",
        }
        comando = [
            str(self.proyecto / "node_modules" / ".bin" / "playwright"),
            "test",
            (trabajo / nombre).relative_to(self.proyecto).as_posix(),
        ]
        try:
            # Grupo de procesos propio: si se agota el tiempo, se cortan también los
            # workers y el navegador que lanza Playwright.
            proceso = subprocess.Popen(
                comando,
                cwd=self.proyecto,
                env=entorno,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
            try:
                log, _ = proceso.communicate(timeout=self.tiempo_maximo_s)
            except subprocess.TimeoutExpired as exc:
                os.killpg(proceso.pid, signal.SIGKILL)
                proceso.communicate()
                minutos = self.tiempo_maximo_s // 60
                raise TiempoAgotado(
                    f"La ejecución superó el tiempo máximo de {minutos} minutos y se cortó."
                ) from exc
        finally:
            shutil.rmtree(trabajo, ignore_errors=True)

        archivo_reporte = salida / "reporte.json"
        reporte = None
        if archivo_reporte.exists():
            try:
                reporte = json.loads(archivo_reporte.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning("El reporte de Playwright %s no es JSON válido", archivo_reporte)
        return SalidaRunner(proceso.returncode, log[-LIMITE_LOG:], reporte)


def obtener_runner() -> Runner:
    return RunnerPlaywright()


RunnerActual = Annotated[Runner, Depends(obtener_runner)]
