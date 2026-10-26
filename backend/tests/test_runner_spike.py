"""Anticipo del runner de S5: Python lanza Playwright con subprocess y lee el reporte JSON."""

import json
import os
import subprocess
from pathlib import Path

import pytest

PROYECTO_PLAYWRIGHT = Path(__file__).resolve().parent.parent / "playwright"


@pytest.mark.slow
def test_playwright_smoke_desde_python(tmp_path):
    entorno = {**os.environ, "PW_SALIDA_DIR": str(tmp_path)}

    proceso = subprocess.run(
        ["npx", "playwright", "test", "smoke"],
        cwd=PROYECTO_PLAYWRIGHT,
        env=entorno,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert proceso.returncode == 0, proceso.stdout + proceso.stderr
    reporte = json.loads((tmp_path / "reporte.json").read_text())
    assert reporte["stats"]["expected"] == 1
    assert reporte["stats"]["unexpected"] == 0
