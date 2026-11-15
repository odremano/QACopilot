"""Identidad de la app: nombre, lema, isotipo y configuración común de cada pantalla."""

from pathlib import Path

import streamlit as st

NOMBRE_APP = "Casewright"
LEMA = "La IA propone, el sistema valida y la persona decide."

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
ISOTIPO = str(_ASSETS / "isotipo.svg")
LOGO = str(_ASSETS / "logo.svg")


def configurar_pagina() -> None:
    """Título de la pestaña, favicon y ancho, iguales en todas las pantallas."""
    st.set_page_config(page_title=NOMBRE_APP, page_icon=ISOTIPO, layout="wide")
