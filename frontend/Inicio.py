"""Punto de entrada de Streamlit: configuración común y navegación entre pantallas (spec 9.2)."""

import streamlit as st

from lib import marca, rutas

marca.configurar_pagina()
st.logo(marca.LOGO, size="large", icon_image=marca.ISOTIPO)

navegacion = st.navigation(
    [
        st.Page(rutas.PANEL, title="Panel", default=True),
        st.Page(rutas.HISTORIAS, title="Historias"),
        st.Page(rutas.DETALLE, title="Detalle de historia"),
        st.Page(rutas.EJECUCIONES, title="Ejecuciones"),
        st.Page(rutas.CATALOGO, title="Catálogo"),
        st.Page(rutas.ACERCA_DE, title="Acerca de"),
    ]
)
navegacion.run()
