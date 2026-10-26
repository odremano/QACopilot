import streamlit as st

from lib import api, rutas
from lib.formato import etiqueta_historia, fecha

st.set_page_config(page_title="QA Copilot", layout="wide")

st.title("QA Copilot")
st.caption("La IA propone, el sistema valida y la persona decide.")

try:
    historias = api.listar_historias()
except api.ErrorApi as error:
    st.error(error.mensaje)
    st.stop()

totales = {"pendiente": 0, "aprobado": 0, "descartado": 0, "invalidos": 0}
for historia in historias:
    for estado in totales:
        totales[estado] += historia["resumen_casos"][estado]

columnas = st.columns(5)
columnas[0].metric("Historias", len(historias))
columnas[1].metric("Casos pendientes", totales["pendiente"])
columnas[2].metric("Casos aprobados", totales["aprobado"])
columnas[3].metric("Casos descartados", totales["descartado"])
columnas[4].metric("Casos inválidos", totales["invalidos"])

st.subheader("Historias recientes")
if not historias:
    st.info("Todavía no hay historias cargadas.")
for historia in historias[:5]:
    resumen = historia["resumen_casos"]
    izquierda, derecha = st.columns([3, 2])
    izquierda.page_link(
        rutas.DETALLE, label=etiqueta_historia(historia), query_params={"id": historia["id"]}
    )
    derecha.caption(
        f"Actualizada: {fecha(historia['actualizada_en'])} · "
        f"{resumen['pendiente']} pendientes · {resumen['aprobado']} aprobados"
    )
st.page_link(rutas.HISTORIAS, label="Ver todas las historias")

st.subheader("Últimas ejecuciones")
st.info("Disponible a partir de S5.")
