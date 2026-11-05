"""Vistas de una ejecución (RF-07, RF-08), compartidas por el Detalle y la pantalla Ejecuciones.

Mientras la ejecución está «en curso», un fragmento la vuelve a pedir cada pocos segundos sin
redibujar el resto de la página, así que se puede seguir usando la interfaz (CA-07). Cuando
termina, se recarga la página completa para actualizar contadores y botones.
"""

from collections.abc import Callable

import streamlit as st

from lib import api, rutas
from lib.formato import (
    duracion_ejecucion,
    etiqueta_resultado,
    fecha,
    porcentaje,
)

INTERVALO_S = 2


def en_vivo(ejecucion: dict, dibujar: Callable[[dict], None]) -> None:
    """Dibuja la ejecución; si está en curso, la actualiza sola hasta que termina."""
    if ejecucion["estado"] != "en_curso":
        dibujar(ejecucion)
        return

    @st.fragment(run_every=INTERVALO_S, key=f"en_vivo_{ejecucion['id']}")
    def actualizar() -> None:
        try:
            actual = api.obtener_ejecucion(ejecucion["id"])
        except api.ErrorApi as error:
            st.error(error.mensaje)
            return
        if actual["estado"] != "en_curso":
            st.rerun()
        dibujar(actual)

    actualizar()


def resumen(ejecucion: dict) -> None:
    """Estado de la última ejecución de una historia, para el Detalle."""
    numero = ejecucion["id"]
    if ejecucion["estado"] == "en_curso":
        st.info(
            f"⏳ Ejecución {numero} en curso desde {fecha(ejecucion['iniciada_en'])} "
            f"({ejecucion['total']} casos). Se actualiza sola; podés seguir usando la app."
        )
    elif ejecucion["estado"] == "error":
        st.error(f"La ejecución {numero} terminó con error: revisá el log en su detalle.")
    else:
        texto = (
            f"Última ejecución ({numero}): {ejecucion['aprobados']} de {ejecucion['total']} "
            f"casos aprobados ({porcentaje(ejecucion['porcentaje_exito'])}) · "
            f"{fecha(ejecucion['finalizada_en'])}"
        )
        if ejecucion["fallidos"] or ejecucion["omitidos"]:
            st.warning(texto)
        else:
            st.success(texto)
    st.page_link(
        rutas.EJECUCIONES,
        label=f"Ver el detalle de la ejecución {numero}",
        query_params={"id": numero},
    )


def detalle(ejecucion: dict) -> None:
    """Totales, resultado de cada caso con su error y su captura, y el log (CA-08)."""
    historia = ejecucion["historia"]
    st.page_link(
        rutas.DETALLE,
        label=f"{historia['codigo']} · {historia['titulo']}",
        query_params={"id": historia["id"]},
    )
    st.caption(
        f"Inicio: {fecha(ejecucion['iniciada_en'])} · Fin: {fecha(ejecucion['finalizada_en'])} "
        f"· Duración: {duracion_ejecucion(ejecucion)}"
    )
    if ejecucion["estado"] == "en_curso":
        st.info(
            f"⏳ Ejecutando {ejecucion['total']} casos contra SauceDemo con Chromium headless. "
            "Esta vista se actualiza sola."
        )
        return

    columnas = st.columns(5)
    columnas[0].metric("Casos", ejecucion["total"])
    columnas[1].metric("Aprobados", ejecucion["aprobados"])
    columnas[2].metric("Fallidos", ejecucion["fallidos"])
    columnas[3].metric("Omitidos", ejecucion["omitidos"])
    columnas[4].metric("Éxito", porcentaje(ejecucion["porcentaje_exito"]))

    if ejecucion["estado"] == "error":
        st.error("La ejecución terminó con error y no hay resultados por caso.")
    for resultado in ejecucion["resultados"]:
        _resultado(resultado)
    if ejecucion["log"]:
        with st.expander("Log de Playwright", expanded=ejecucion["estado"] == "error"):
            st.code(ejecucion["log"], language=None, wrap_lines=True)


def _resultado(resultado: dict) -> None:
    with st.expander(etiqueta_resultado(resultado), expanded=resultado["estado"] == "fallido"):
        if resultado["mensaje_error"]:
            st.code(resultado["mensaje_error"], language=None, wrap_lines=True)
        else:
            st.caption("Todos los pasos se cumplieron.")
        if resultado["url_captura"]:
            try:
                captura = api.obtener_captura(resultado["url_captura"])
            except api.ErrorApi as error:
                st.warning(f"No se pudo cargar la captura: {error.mensaje}")
            else:
                st.image(captura, caption="Captura de pantalla en el momento del fallo", width=900)
