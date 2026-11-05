import streamlit as st

from lib import api, vista_ejecuciones
from lib.formato import (
    ESTADOS_EJECUCION,
    duracion_ejecucion,
    etiqueta_ejecucion,
    etiqueta_historia,
    fecha,
    porcentaje,
)

st.set_page_config(page_title="QA Copilot", layout="wide")

st.title("Ejecuciones")
st.caption("Ejecuciones contra SauceDemo con el resultado de cada caso y sus capturas.")

try:
    historias = api.listar_historias()
except api.ErrorApi as error:
    st.error(error.mensaje)
    st.stop()

filtro = st.selectbox(
    "Historia",
    [None, *historias],
    format_func=lambda h: "Todas" if h is None else etiqueta_historia(h),
)
try:
    ejecuciones = api.listar_ejecuciones(None if filtro is None else filtro["id"])
except api.ErrorApi as error:
    st.error(error.mensaje)
    st.stop()

if not ejecuciones:
    st.info(
        "Todavía no hay ejecuciones. Aprobá casos en el Detalle de una historia y "
        "presioná «Ejecutar pruebas»."
    )
    st.stop()

st.dataframe(
    [
        {
            "Ejecución": e["id"],
            "Historia": f"{e['historia']['codigo']} · {e['historia']['titulo']}",
            "Estado": ESTADOS_EJECUCION.get(e["estado"], e["estado"]),
            "Inicio": fecha(e["iniciada_en"]),
            "Duración": duracion_ejecucion(e),
            "Casos": e["total"],
            "Aprobados": e["aprobados"],
            "Fallidos": e["fallidos"],
            "Omitidos": e["omitidos"],
            "Éxito": porcentaje(e["porcentaje_exito"]),
        }
        for e in ejecuciones
    ],
    hide_index=True,
)

# La ejecución llega por ?id=3 (desde el Detalle); si no, se muestra la más reciente.
ids = [e["id"] for e in ejecuciones]
id_pedido = st.query_params.get("id")
indice = 0
if id_pedido is not None:
    if id_pedido.isdigit() and int(id_pedido) in ids:
        indice = ids.index(int(id_pedido))
    else:
        st.warning(f"La ejecución {id_pedido} no está en el listado. Elegí otra.")

st.subheader("Detalle")
elegida = st.selectbox("Ejecución", ejecuciones, index=indice, format_func=etiqueta_ejecucion)
st.query_params["id"] = str(elegida["id"])

try:
    ejecucion = api.obtener_ejecucion(elegida["id"])
except api.ErrorApi as error:
    st.error(error.mensaje)
    st.stop()

vista_ejecuciones.en_vivo(ejecucion, vista_ejecuciones.detalle)
